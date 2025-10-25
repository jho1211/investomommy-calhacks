import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Search, AlertCircle } from "lucide-react";

const Analyze = () => {
  const [ticker, setTicker] = useState("");
  const navigate = useNavigate();

  const handleAnalyze = () => {
    if (ticker.trim()) {
      navigate(`/dashboard/${ticker.toUpperCase()}`);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Analyze a Stock</h1>
          <p className="text-lg text-muted-foreground">
            Enter a ticker symbol to get comprehensive AI-powered analysis including financial metrics and sentiment analysis of related news headlines.
          </p>
        </div>

        <Card className="max-w-2xl mx-auto mb-16">
          <CardContent className="pt-8 pb-8">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="h-6 w-6 text-primary" />
              <h2 className="text-2xl font-bold">Stock Analysis</h2>
            </div>
            <p className="text-muted-foreground mb-6">
              Get detailed insights powered by AI and real-time market data
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Stock Ticker Symbol</label>
                <Input 
                  placeholder="e.g., AAPL, GOOGL, TSLA"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                  className="text-lg"
                />
                <p className="text-sm text-muted-foreground mt-2">
                  Enter the ticker symbol of the stock you want to analyze
                </p>
              </div>
              
              <Button 
                onClick={handleAnalyze} 
                className="w-full" 
                size="lg"
                disabled={!ticker.trim()}
              >
                Analyze Stock
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <Card>
            <CardContent className="pt-6 text-center">
              <TrendingUp className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-bold text-lg mb-2">Financial Metrics</h3>
              <p className="text-sm text-muted-foreground">
                Get comprehensive financial data including P/E ratios, market cap, and more
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6 text-center">
              <Search className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-bold text-lg mb-2">AI Sentiment Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Advanced sentiment analysis of recent news headlines and market sentiment
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6 text-center">
              <AlertCircle className="h-12 w-12 text-primary mx-auto mb-4" />
              <h3 className="font-bold text-lg mb-2">Investment Assessment</h3>
              <p className="text-sm text-muted-foreground">
                Clear buy, hold, or sell assessments based on comprehensive analysis
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Analyze;
