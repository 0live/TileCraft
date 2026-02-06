import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight } from "lucide-react";

interface StepNavigationProps {
  onBack?: () => void;
  onNext?: () => void;
  canNext?: boolean;
  canBack?: boolean;
  isLastStep?: boolean;
  isNectProcessing?: boolean;
  nextLabel?: string;
}

export function StepNavigation({ 
  onBack, 
  onNext, 
  canNext = true, 
  canBack = true, 
  isLastStep = false,
  isNectProcessing = false,
  nextLabel
}: StepNavigationProps) {
  return (
    <div className="flex justify-between mt-8 pt-4 border-t">
      <Button 
        variant="outline" 
        onClick={onBack} 
        disabled={!canBack}
        className={!canBack ? "invisible" : ""}
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back
      </Button>
      
      <Button 
        onClick={onNext} 
        disabled={!canNext || isNectProcessing}
      >
        {isNectProcessing ? 'Processing...' : (nextLabel || (isLastStep ? 'Import' : 'Next'))}
        {!isLastStep && !isNectProcessing && <ArrowRight className="w-4 h-4 ml-2" />}
      </Button>
    </div>
  );
}
