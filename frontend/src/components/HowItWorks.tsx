import { UserCheck, CheckCircle2, Gift, FileText } from 'lucide-react';

export function HowItWorks() {
  const steps = [
    {
      number: '01',
      title: 'Tell us about yourself',
      description: 'Answer simple profile questions including your occupation, landholding, state, and income.',
      icon: UserCheck,
      color: 'bg-blue-50 text-blue-700 border-blue-100',
    },
    {
      number: '02',
      title: 'GramSetu checks eligibility',
      description: 'Our deterministic rule engine compares your profile against statutory scheme conditions.',
      icon: CheckCircle2,
      color: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    },
    {
      number: '03',
      title: 'Understand your benefits',
      description: 'Review transparent match explanations, direct financial assistance, and subsidy amounts.',
      icon: Gift,
      color: 'bg-amber-50 text-amber-700 border-amber-100',
    },
    {
      number: '04',
      title: 'Prepare your application',
      description: 'Access an itemized required document checklist and direct links to official ministry portals.',
      icon: FileText,
      color: 'bg-indigo-50 text-indigo-700 border-indigo-100',
    },
  ];

  return (
    <section className="py-16 bg-white border-b border-slate-200/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h2 className="text-xs font-bold text-emerald-700 uppercase tracking-widest">
            Simple 4-Step Process
          </h2>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            How GramSetu Works
          </h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            Eliminating bureaucratic complexity and intermediaries so every eligible citizen receives their statutory entitlements.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.number}
                className="bg-slate-50 rounded-2xl p-6 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow relative flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className={`p-3 rounded-2xl border ${step.color}`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <span className="text-xl font-black text-slate-300 font-mono">
                      {step.number}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-bold text-base text-slate-900">{step.title}</h4>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
