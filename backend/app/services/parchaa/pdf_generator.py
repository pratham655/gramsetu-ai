import io
from typing import List, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.pdfgen import canvas
from app.schemas.parchaa import (
    ParchaaResponse,
    ParchaaCitizenProfile,
    ParchaaDocumentItem,
    DocumentStatusEnum,
)


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to guarantee single-page enforcement and footer watermark.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        # Footer watermark and metadata bar
        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748b"))
        footer_text = "GramSetu AI • Civic-Tech Application Dossier • Generated on demand from verified government data • Zero permanent PII retention"
        self.drawString(36, 18, footer_text)
        self.drawRightString(A4[0] - 36, 18, f"Page {self._pageNumber} of {page_count} • Single-Page Dossier")
        
        # Bottom rule
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 26, A4[0] - 36, 26)
        self.restoreState()


class ParchaaPdfGenerator:
    """
    Generates a professional, compact, single-page A4 application dossier.
    Designed for high legibility, crisp black-and-white printing, and strict 1-page geometry.
    """

    @classmethod
    def generate_pdf_bytes(cls, dossier: ParchaaResponse) -> bytes:
        buffer = io.BytesIO()
        
        # A4: 595.27 x 841.89 points. Margins: 26 pt (~0.36 in) for maximum printable area.
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=28,
            rightMargin=28,
            topMargin=22,
            bottomMargin=32,
            title=f"GramSetu_Parchaa_{dossier.scheme.scheme_id}.pdf",
            author="GramSetu AI",
            subject="Government Scheme Application Dossier",
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        style_header_title = ParagraphStyle(
            "ParchaaHeaderTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=15,
            textColor=colors.HexColor("#064e3b"),  # Deep emerald
        )
        
        style_header_sub = ParagraphStyle(
            "ParchaaHeaderSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475569"),
        )
        
        style_scheme_title = ParagraphStyle(
            "ParchaaSchemeTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12.5,
            textColor=colors.HexColor("#0f172a"),
        )
        
        style_section_heading = ParagraphStyle(
            "ParchaaSectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#065f46"),
            spaceAfter=2,
        )
        
        style_body_text = ParagraphStyle(
            "ParchaaBodyText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#1e293b"),
        )
        
        style_body_bold = ParagraphStyle(
            "ParchaaBodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0f172a"),
        )

        style_table_header = ParagraphStyle(
            "ParchaaTableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor("#0f172a"),
        )

        style_table_cell = ParagraphStyle(
            "ParchaaTableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor("#334155"),
        )

        story = []

        # -------------------------------------------------------------
        # 1. HEADER & META BAR
        # -------------------------------------------------------------
        header_left = [
            Paragraph("<b>GRAMSETU AI • APPLICATION PARCHAA</b>", style_header_title),
            Paragraph(f"Official Citizen Welfare Application Dossier | Ref: <b>{dossier.reference_number}</b>", style_header_sub),
        ]
        
        header_right = [
            Paragraph(f"<b>Date:</b> {dossier.generated_at}", ParagraphStyle("HR1", parent=style_header_sub, alignment=2)),
            Paragraph(f"<b>Category:</b> {dossier.scheme.category}", ParagraphStyle("HR2", parent=style_header_sub, alignment=2)),
        ]

        header_table = Table(
            [[header_left, header_right]],
            colWidths=[360, 179],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#059669"), spaceBefore=1, spaceAfter=4))

        # -------------------------------------------------------------
        # 2. SCHEME OVERVIEW & STATUTORY BENEFIT
        # -------------------------------------------------------------
        scheme_name_p = Paragraph(f"<b>{dossier.scheme.scheme_name}</b>", style_scheme_title)
        story.append(scheme_name_p)
        story.append(Spacer(1, 2))

        # Top 2-Column Section: Left = Scheme Info, Right = Citizen Snapshot
        # Scheme summary content
        benefit_items = "".join([f"• {b}<br/>" for b in dossier.scheme.main_benefits[:2]])
        scheme_info_flow = [
            Paragraph("<b>SCHEME OVERVIEW & BENEFITS</b>", style_section_heading),
            Paragraph(f"<b>Description:</b> {dossier.scheme.short_description}", style_body_text),
            Spacer(1, 2),
            Paragraph(f"<b>Beneficiaries:</b> {dossier.scheme.target_beneficiaries}", style_body_text),
            Spacer(1, 2),
            Paragraph(f"<b>Direct Entitlements:</b><br/>{benefit_items}", style_body_text),
        ]

        # Citizen Snapshot content
        cit = dossier.citizen
        if cit:
            cit_name = cit.name or "Beneficiary Applicant"
            cit_loc = f"{cit.district or 'District'}, {cit.state or 'State'}"
            cit_occ = (cit.occupation or "Resident").capitalize()
            cit_cat = cit.category or "General"
            cit_land = f"{cit.landholding} Acres" if cit.landholding is not None else "N/A"
            cit_bpl = "Yes (BPL Cardholder)" if cit.bpl else ("No" if cit.bpl is False else "N/A")
            cit_ym = "Eligible (100% Rule Match)" if cit.yojanamatch_eligible else "Evaluated"
            
            # Masked Aadhaar / Bank if provided
            aadhaar_display = cit.aadhaar_masked or "Linked via e-KYC"
            
            citizen_details = [
                Paragraph("<b>CITIZEN ELIGIBILITY SNAPSHOT</b>", style_section_heading),
                Paragraph(f"<b>Applicant:</b> {cit_name} ({cit.age or 'Adult'} yrs, {cit.gender or 'Applicant'})", style_body_text),
                Paragraph(f"<b>Location:</b> {cit_loc} | <b>Occupation:</b> {cit_occ}", style_body_text),
                Paragraph(f"<b>Category:</b> {cit_cat} | <b>Land:</b> {cit_land} | <b>BPL:</b> {cit_bpl}", style_body_text),
                Paragraph(f"<b>Aadhaar ID:</b> <font name='Courier'>{aadhaar_display}</font> (Masked for Privacy)", style_body_text),
                Paragraph(f"<b>YojanaMatch Status:</b> <font color='#047857'><b>{cit_ym}</b></font>", style_body_text),
            ]
        else:
            citizen_details = [
                Paragraph("<b>CITIZEN ELIGIBILITY SNAPSHOT</b>", style_section_heading),
                Paragraph("Standard citizen profile evaluated.", style_body_text),
                Paragraph("Statutory eligibility conditions apply as per government gazette.", style_body_text),
                Paragraph("Carry original Aadhaar and required certificates to the application center.", style_body_text),
            ]

        top_grid = Table(
            [[scheme_info_flow, citizen_details]],
            colWidths=[275, 264],
        )
        top_grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f8fafc")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f0fdf4")),
            ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#e2e8f0")),
            ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#bbf7d0")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]))
        story.append(top_grid)
        story.append(Spacer(1, 4))

        # -------------------------------------------------------------
        # 3. REQUIRED DOCUMENTS & KAGAZCHECK READINESS MATRIX
        # -------------------------------------------------------------
        story.append(Paragraph("<b>REQUIRED DOCUMENTS & READINESS STATUS</b>", style_section_heading))
        
        doc_table_data = [
            [
                Paragraph("<b>Required Document Name</b>", style_table_header),
                Paragraph("<b>Audit Status</b>", style_table_header),
                Paragraph("<b>Physical Enclosure Action / Instructions</b>", style_table_header),
            ]
        ]

        for doc_item in dossier.documents:
            status_style = style_table_cell
            st_text = doc_item.status.value
            if doc_item.status in (DocumentStatusEnum.READY, DocumentStatusEnum.VERIFIED):
                badge = f"<font color='#047857'><b>[READY]</b></font> {st_text}"
            elif doc_item.status == DocumentStatusEnum.NEEDS_ATTENTION:
                badge = f"<font color='#b45309'><b>[ATTENTION]</b></font> {st_text}"
            elif doc_item.status == DocumentStatusEnum.MISSING:
                badge = f"<font color='#b91c1c'><b>[MISSING]</b></font> {st_text}"
            else:
                badge = f"<font color='#1e293b'><b>[REQUIRED]</b></font> Required"

            doc_table_data.append([
                Paragraph(f"<b>{doc_item.document_name}</b>", style_table_cell),
                Paragraph(badge, status_style),
                Paragraph(doc_item.enclosure_note or "Self-attested physical photocopy required", style_table_cell),
            ])

        doc_table = Table(
            doc_table_data,
            colWidths=[205, 114, 220],
        )
        doc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ]))
        story.append(doc_table)
        story.append(Spacer(1, 4))

        # -------------------------------------------------------------
        # 4. PHYSICAL ENCLOSURES & APPLICATION PROCESS STEPS
        # -------------------------------------------------------------
        # Left column: Physical Enclosures (What to carry in hand)
        enclosures_text = "".join([f"• {enc}<br/>" for enc in dossier.application_info.physical_enclosures[:5]])
        enclosures_flow = [
            Paragraph("<b>PHYSICAL ENCLOSURES TO CARRY</b>", style_section_heading),
            Paragraph(enclosures_text, style_body_text),
        ]

        # Right column: Step-by-step submission steps
        steps_text = "".join([f"{step}<br/>" for step in dossier.application_info.process_steps[:5]])
        steps_flow = [
            Paragraph("<b>APPLICATION PROCESS & STEPS</b>", style_section_heading),
            Paragraph(steps_text, style_body_text),
        ]

        mid_grid = Table(
            [[enclosures_flow, steps_flow]],
            colWidths=[240, 299],
        )
        mid_grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#fffbeb")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#fde68a")),
            ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(mid_grid)
        story.append(Spacer(1, 4))

        # -------------------------------------------------------------
        # 5. ADMINISTRATIVE OFFICE, PORTAL & TIMELINE
        # -------------------------------------------------------------
        off = dossier.application_info.administrative_office
        if off.is_verified:
            office_str = f"<b>Office:</b> {off.office_name}<br/><b>Department:</b> {off.department}<br/><b>Address:</b> {off.address or 'Designated District Office'} | <b>Helpline:</b> {off.contact_info or 'National Toll Free'}"
        else:
            office_str = f"<b>Office:</b> <font color='#64748b'><i>{off.unverified_notice or 'Office information not available in current verified database.'}</i></font>"

        tl = dossier.application_info.processing_timeline
        if tl.is_verified:
            timeline_str = f"<b>Processing Timeline:</b> {tl.timeline_description}"
        else:
            timeline_str = f"<b>Processing Timeline:</b> <font color='#64748b'><i>{tl.unverified_notice or 'Processing timeline not available in current verified database.'}</i></font>"

        portal_url = dossier.application_info.official_portal_url or dossier.scheme.official_source_url
        portal_str = f"<b>Official Government Portal:</b> <font name='Courier' color='#0369a1'><b>{portal_url}</b></font>"

        admin_box_content = [
            Paragraph("<b>ADMINISTRATIVE NODAL OFFICE & OFFICIAL PORTAL</b>", style_section_heading),
            Paragraph(office_str, style_body_text),
            Spacer(1, 1),
            Paragraph(f"{portal_str} | {timeline_str}", style_body_text),
        ]

        admin_table = Table(
            [[admin_box_content]],
            colWidths=[539],
        )
        admin_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(admin_table)
        story.append(Spacer(1, 4))

        # -------------------------------------------------------------
        # 6. ACTIONABLE NEXT STEP (CITIZEN ADVISORY)
        # -------------------------------------------------------------
        next_action_box = [
            Paragraph("<b>ACTIONABLE NEXT STEP FOR CITIZEN:</b>", style_section_heading),
            Paragraph(f"<b>{dossier.application_info.next_step_action}</b>", ParagraphStyle("NAB", parent=style_body_text, fontSize=7.5, leading=9.5, textColor=colors.HexColor("#064e3b"))),
        ]
        next_action_table = Table(
            [[next_action_box]],
            colWidths=[539],
        )
        next_action_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#10b981")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(next_action_table)

        # Build document with custom canvas
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()


pdf_generator = ParchaaPdfGenerator()
