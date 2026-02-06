import { Check } from 'lucide-react';

interface StepperProps {
  currentStep: number;
  steps: string[];
}

export function Stepper({ currentStep, steps }: StepperProps) {
  return (
    <div className="flex items-center justify-center w-full mb-8">
      {steps.map((step, index) => {
        const stepNumber = index + 1;
        const isCompleted = currentStep > stepNumber;
        const isCurrent = currentStep === stepNumber;

        return (
          <div key={step} className="flex items-center">
            <div className="relative flex flex-col items-center group">
              <div
                className={`
                  flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors duration-200
                  ${isCompleted ? 'bg-primary border-primary text-primary-foreground' : ''}
                  ${isCurrent ? 'border-primary text-primary' : ''}
                  ${!isCompleted && !isCurrent ? 'border-muted text-muted-foreground' : ''}
                `}
              >
                {isCompleted ? <Check className="w-6 h-6" /> : <span>{stepNumber}</span>}
              </div>
              <div className={`absolute top-12 text-xs font-medium whitespace-nowrap ${isCurrent ? 'text-foreground' : 'text-muted-foreground'}`}>
                {step}
              </div>
            </div>
            {index < steps.length - 1 && (
              <div
                className={`
                  w-24 h-0.5 mx-2 transition-colors duration-200
                  ${isCompleted ? 'bg-primary' : 'bg-muted'}
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
