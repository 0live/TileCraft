import { Card, CardContent } from "@/components/ui/card";
import { Stepper } from './components/Stepper';
import { Step1Source } from './steps/Step1Source';
import { Step2Metadata } from './steps/Step2Metadata';
import { Step3Preview } from './steps/Step3Preview';
import { useImportStore } from './store';

export function ImportWizard() {
  const { step } = useImportStore();

  return (
    <div className="container mx-auto max-w-4xl py-10 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Import Data</h1>
        <p className="text-muted-foreground">
            Follow the steps to import geospatial data into Canopy.
        </p>
      </div>

      <Card className="border-none shadow-md bg-card/50 backdrop-blur-sm">
        <CardContent className="pt-6">
            <Stepper 
                currentStep={step} 
                steps={['Source', 'Metadata', 'Preview']} 
            />
            
            <div className="mt-8 min-h-[400px]">
                {step === 1 && <Step1Source />}
                {step === 2 && <Step2Metadata />}
                {step === 3 && <Step3Preview />}
            </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Default export for route lazy loading
export default ImportWizard;
