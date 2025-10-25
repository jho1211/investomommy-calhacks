import Navigation from "@/components/Navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Search, BarChart3, TrendingUp, CheckCircle } from "lucide-react";

const HowItWorks = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-center mb-4">How it Works</h1>
          <p className="text-center text-muted-foreground mb-12 text-lg">
            Get comprehensive stock analysis in four simple steps
          </p>

          <div className="space-y-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="bg-primary text-primary-foreground rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl flex-shrink-0">
                    1
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Search className="h-6 w-6 text-primary" />
                      <h3 className="font-bold text-xl">Enter a Stock Ticker</h3>
                    </div>
                    <p className="text-muted-foreground">
                      Start by entering the ticker symbol of the stock you want to analyze (e.g., AAPL for Apple, TSLA for Tesla). Our system will pull the latest market data.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="bg-primary text-primary-foreground rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl flex-shrink-0">
                    2
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="h-6 w-6 text-primary" />
                      <h3 className="font-bold text-xl">AI-Powered Analysis</h3>
                    </div>
                    <p className="text-muted-foreground">
                      Our system runs multiple valuation models including DCF analysis, relative valuation, and Monte Carlo simulations. We also analyze recent news headlines using natural language processing.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="bg-primary text-primary-foreground rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl flex-shrink-0">
                    3
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="h-6 w-6 text-primary" />
                      <h3 className="font-bold text-xl">View Your Dashboard</h3>
                    </div>
                    <p className="text-muted-foreground">
                      See a comprehensive dashboard with four key analysis cards: Relative Valuation, Absolute Valuation (DCF), Monte Carlo Simulation, and News Sentiment Analysis.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="bg-primary text-primary-foreground rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl flex-shrink-0">
                    4
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-6 w-6 text-primary" />
                      <h3 className="font-bold text-xl">Make Informed Decisions</h3>
                    </div>
                    <p className="text-muted-foreground">
                      Click "Details" on any card to learn what each analysis means in beginner-friendly language. Use these insights to make informed investment decisions.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-12 bg-secondary/30">
            <CardContent className="pt-6">
              <h3 className="font-bold text-xl mb-4">Important Notes</h3>
              <ul className="space-y-2 text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  <span>All analysis is for educational purposes only and does not constitute financial advice</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  <span>We show you all our calculations and methods so you can understand how we reach our conclusions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  <span>You should always do your own research and consult with a financial advisor before making investment decisions</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HowItWorks;
