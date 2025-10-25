import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Scale, TrendingUp, BarChart3, Newspaper, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";

type DetailType = "relative" | "absolute" | "montecarlo" | "sentiment" | null;

const Dashboard = () => {
  const { ticker = "TSLA" } = useParams();
  const [openDetail, setOpenDetail] = useState<DetailType>(null);
  const [showComparePicker, setShowComparePicker] = useState(false);
  const [selectedComparisonTicker, setSelectedComparisonTicker] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    // Show notification prompting user to select comparison stock
    if (!selectedComparisonTicker) {
      const timer = setTimeout(() => {
        toast({
          title: "Action Required",
          description: `Select a comparable stock to analyze ${ticker} using Relative Valuation`,
          action: (
            <Button variant="secondary" size="sm" onClick={() => setShowComparePicker(true)}>
              Select Stock
            </Button>
          ),
          duration: 8000,
        });
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [ticker, selectedComparisonTicker, toast]);

  // Mock data - will be replaced with real sector data from backend
  const comparableTickers = [
    { symbol: "AAPL", name: "Apple Inc." },
    { symbol: "MSFT", name: "Microsoft Corporation" },
    { symbol: "GOOGL", name: "Alphabet Inc." },
    { symbol: "AMZN", name: "Amazon.com Inc." },
    { symbol: "META", name: "Meta Platforms Inc." },
    { symbol: "NVDA", name: "NVIDIA Corporation" },
    { symbol: "BRK.B", name: "Berkshire Hathaway Inc." },
    { symbol: "JPM", name: "JPMorgan Chase & Co." },
    { symbol: "V", name: "Visa Inc." },
    { symbol: "WMT", name: "Walmart Inc." },
  ];

  const handleComparisonSelect = (symbol: string) => {
    setSelectedComparisonTicker(symbol);
    setShowComparePicker(false);
    toast({
      title: "Comparison Stock Selected",
      description: `Now comparing ${ticker} with ${symbol}`,
    });
    // Analysis will be triggered here when backend is connected
  };

  const detailContent = {
    relative: {
      title: "Relative Valuation",
      icon: <Scale className="h-6 w-6 text-primary" />,
      description: "Compare stocks using price multiples",
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Relative valuation helps you compare similar companies by looking at their price multiples. Think of it like comparing houses in a neighborhood - you want to see if you're getting a good deal compared to similar properties.
          </p>
          
          <div className="bg-secondary/30 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">Common Metrics:</h4>
            <ul className="space-y-2 text-sm">
              <li><strong>P/E Ratio:</strong> How much you pay per dollar of earnings</li>
              <li><strong>P/B Ratio:</strong> Price compared to the company's book value</li>
              <li><strong>P/S Ratio:</strong> Price compared to sales revenue</li>
            </ul>
          </div>
          
          <p className="text-muted-foreground">
            If a stock has much higher multiples than its peers, it might be overvalued. If it's much lower, it could be undervalued - or there might be a good reason for the discount.
          </p>
        </div>
      ),
    },
    absolute: {
      title: "Absolute Valuation (DCF Model)",
      icon: <TrendingUp className="h-6 w-6 text-primary" />,
      description: "Determine intrinsic stock value",
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            The Discounted Cash Flow (DCF) model calculates what a stock is actually worth based on the money the company is expected to make in the future. It's like figuring out how much a money tree is worth by estimating all the fruit it will produce.
          </p>
          
          <div className="bg-secondary/30 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">How It Works:</h4>
            <ol className="space-y-2 text-sm list-decimal list-inside">
              <li>Estimate future cash flows (money the company will make)</li>
              <li>Discount them to today's value (money today is worth more than money later)</li>
              <li>Compare this "intrinsic value" to the current stock price</li>
            </ol>
          </div>
          
          <p className="text-muted-foreground">
            If the intrinsic value is higher than the current price, the stock might be undervalued and worth buying. If it's lower, the stock might be overvalued.
          </p>
        </div>
      ),
    },
    montecarlo: {
      title: "Monte Carlo Simulation",
      icon: <BarChart3 className="h-6 w-6 text-primary" />,
      description: "Visualize price uncertainty",
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Monte Carlo simulation is like running thousands of "what if" scenarios to see all the possible outcomes for a stock's price. Imagine rolling dice thousands of times to understand all the possible results.
          </p>
          
          <div className="bg-secondary/30 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">What It Shows:</h4>
            <ul className="space-y-2 text-sm">
              <li><strong>Range of Outcomes:</strong> Best case, worst case, and everything in between</li>
              <li><strong>Probability Distribution:</strong> Which outcomes are most likely</li>
              <li><strong>Risk Assessment:</strong> How volatile the stock might be</li>
            </ul>
          </div>
          
          <p className="text-muted-foreground">
            This helps you understand the uncertainty and risk involved. A wide range means high uncertainty; a narrow range means more predictable outcomes.
          </p>
        </div>
      ),
    },
    sentiment: {
      title: "News Headline Sentiment Analysis",
      icon: <Newspaper className="h-6 w-6 text-primary" />,
      description: "AI-powered news sentiment",
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Our AI reads recent financial news headlines about the stock and determines whether the overall sentiment is positive, negative, or neutral. It's like having someone read all the news for you and tell you if it's good or bad.
          </p>
          
          <div className="bg-secondary/30 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">What We Analyze:</h4>
            <ul className="space-y-2 text-sm">
              <li><strong>Recent Headlines:</strong> Latest news from trusted financial sources</li>
              <li><strong>Sentiment Score:</strong> Overall positive, negative, or neutral tone</li>
              <li><strong>Key Themes:</strong> Common topics in the news</li>
            </ul>
          </div>
          
          <p className="text-muted-foreground">
            Positive sentiment might indicate good news is driving the stock up, while negative sentiment could signal concerns. However, sentiment should be just one factor in your decision-making.
          </p>
        </div>
      ),
    },
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-2">{ticker}</h1>
          <p className="text-muted-foreground">Comprehensive Stock Analysis</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {/* Relative Valuation Card */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2 mb-2">
                <Scale className="h-6 w-6 text-primary" />
                <CardTitle>Relative Valuation</CardTitle>
              </div>
              <CardDescription>
                Compare {ticker} with similar companies using price multiples like P/E, P/B, and P/S ratios
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedComparisonTicker ? (
                <div className="bg-secondary/30 p-4 rounded-lg mb-4 border-2 border-dashed border-primary/30">
                  <div className="flex items-center gap-2 mb-2">
                    <ArrowRight className="h-5 w-5 text-primary animate-pulse" />
                    <p className="text-sm font-medium">Action Required</p>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Select a comparable stock to begin analysis
                  </p>
                </div>
              ) : (
                <div className="bg-secondary/30 p-4 rounded-lg mb-4">
                  <p className="text-sm text-muted-foreground mb-2">
                    Comparing with: <Badge variant="secondary">{selectedComparisonTicker}</Badge>
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Analysis based on comparative metrics with industry peers
                  </p>
                </div>
              )}
              <div className="space-y-2">
                <Button 
                  onClick={() => setShowComparePicker(true)}
                  variant="outline"
                  className="w-full"
                >
                  {selectedComparisonTicker ? 'Change Comparison Stock' : `Compare ${ticker} to Another Stock`}
                </Button>
                {selectedComparisonTicker && (
                  <Button 
                    onClick={() => setOpenDetail("relative")}
                    className="w-full"
                  >
                    View Details
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Absolute Valuation Card */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-6 w-6 text-primary" />
                <CardTitle>Absolute Valuation (DCF)</CardTitle>
              </div>
              <CardDescription>
                Discounted Cash Flow model to determine if {ticker} is currently overvalued or undervalued
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-secondary/30 p-4 rounded-lg mb-4">
                <p className="text-sm text-muted-foreground">
                  Intrinsic value calculation based on projected cash flows
                </p>
              </div>
              <Button 
                onClick={() => setOpenDetail("absolute")}
                className="w-full"
              >
                View Details
              </Button>
            </CardContent>
          </Card>

          {/* Monte Carlo Simulation Card */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="h-6 w-6 text-primary" />
                <CardTitle>Monte Carlo Simulation</CardTitle>
              </div>
              <CardDescription>
                Statistical model showing the uncertainty distribution for {ticker}'s potential price movements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-secondary/30 p-4 rounded-lg mb-4">
                <p className="text-sm text-muted-foreground">
                  Probability-based price projection analysis
                </p>
              </div>
              <Button 
                onClick={() => setOpenDetail("montecarlo")}
                className="w-full"
              >
                View Details
              </Button>
            </CardContent>
          </Card>

          {/* News Sentiment Card */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2 mb-2">
                <Newspaper className="h-6 w-6 text-primary" />
                <CardTitle>News Sentiment Analysis</CardTitle>
              </div>
              <CardDescription>
                AI-powered analysis of recent financial news headlines and market sentiment for {ticker}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-secondary/30 p-4 rounded-lg mb-4">
                <p className="text-sm text-muted-foreground">
                  Natural language processing of recent news articles
                </p>
              </div>
              <Button 
                onClick={() => setOpenDetail("sentiment")}
                className="w-full"
              >
                View Details
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Detail Sidebar */}
      <Sheet open={openDetail !== null} onOpenChange={() => setOpenDetail(null)}>
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <div className="flex items-center gap-2 mb-2">
              {openDetail && detailContent[openDetail].icon}
              <SheetTitle>{openDetail && detailContent[openDetail].title}</SheetTitle>
            </div>
            <SheetDescription>
              {openDetail && detailContent[openDetail].description}
            </SheetDescription>
          </SheetHeader>
          <div className="mt-6">
            {openDetail && detailContent[openDetail].content}
          </div>
        </SheetContent>
      </Sheet>

      {/* Comparison Stock Picker Sidebar */}
      <Sheet open={showComparePicker} onOpenChange={setShowComparePicker}>
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Select a Comparable Stock</SheetTitle>
            <SheetDescription>
              Choose from top 10 stocks in the same sector (S&P 500)
            </SheetDescription>
          </SheetHeader>
          <div className="mt-6 space-y-2">
            {comparableTickers.map((stock) => (
              <Button
                key={stock.symbol}
                variant="outline"
                className="w-full justify-start h-auto py-3"
                onClick={() => handleComparisonSelect(stock.symbol)}
              >
                <div className="text-left">
                  <div className="font-semibold">{stock.symbol}</div>
                  <div className="text-sm text-muted-foreground">{stock.name}</div>
                </div>
              </Button>
            ))}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default Dashboard;
