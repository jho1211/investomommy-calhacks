import Navigation from "@/components/Navigation";
import { AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const Disclaimer = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto text-center mb-8">
          <AlertTriangle className="h-16 w-16 text-warning mx-auto mb-4" />
          <h1 className="text-4xl font-bold mb-4">Important Disclaimer</h1>
          <p className="text-muted-foreground text-lg">
            Please read this disclaimer carefully before using InvestoMommy
          </p>
        </div>

        <Card className="max-w-4xl mx-auto">
          <CardContent className="pt-8 pb-8">
            <h2 className="text-2xl font-bold mb-4">Investment Disclaimer</h2>
            <p className="text-muted-foreground leading-relaxed">
              This website and its tools are provided for informational and educational purposes only and do not constitute financial or investment advice. All investment decisions are made at your own risk, and you should conduct your own research or consult with a licensed financial advisor before making any financial decisions. The creators of this tool are not responsible for any losses, financial or otherwise, that may result from the use of this website. By using this site, you acknowledge that you are solely responsible for your investment decisions. This tool is intended solely to assist users in evaluating financial data and does not guarantee or predict stock performance.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Disclaimer;
