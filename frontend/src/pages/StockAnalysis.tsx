// src/pages/StockAnalysis.tsx
import { useParams, Navigate } from "react-router-dom";
import { useState, useEffect, useMemo } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Scale, TrendingUp, BarChart3, Newspaper, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import AddToWatchlistButton from "@/components/AddToWatchlistButton";

type DetailType = "relative" | "absolute" | "montecarlo" | "sentiment" | null;

type MultiplesData = {
  ticker: string;
  price_to_earnings: number | null;
  ev_to_ebitda: number | null;
  ev_to_ebit: number | null;
  price_to_book: number | null;
  debt_to_equity: number | null;
  ev_to_invested_capital: number | null;
  ev_to_fcf: number | null;
  price_to_cash_flow: number | null;
  ev_to_sales: number | null;
  ev_to_revenue_per_employee: number | null;
};

type MonteCarloData = {
  ticker: string;
  spot_price: number;
  mu_annual: number;
  sigma_annual: number;
  mean_return: number;
  std_return: number;
  var95_return: number;
  es95_return: number;
  mean_pnl: number;
  std_pnl: number;
  var95_pnl: number;
  es95_pnl: number;
  histogram_url: string;
  paths_url: string;
  params: {
    years_history: number;
    horizon_years: number;
    steps_per_year: number;
    n_paths: number;
  };
};

type ResearchData = {
  analysis_date: string;
  analysis_data: {
    company_overview: string[];
    business_segments: string[];
    revenue_characteristics: string[];
    geographic_breakdown: string[];
    stakeholders: string[];
    key_performance_indicators: string[];
    valuation: string[];
    recent_news: string[];
    forensic_red_flags: string[];
  };
  created_at: string;
};

type NewsSentimentItem = {
  id: number;
  ticker: string;
  headline: string;
  summary: string | null;
  url: string;
  datetime: string;
  sentiment: "positive" | "negative" | "neutral";
  confidence: number;
  created_at: string;
};

type OverallNewsSentiment = {
  ticker: string;
  date: string;
  total_articles: number;
  positive_ratio: number;
  neutral_ratio: number;
  negative_ratio: number;
  created_at: string;
};

type AnalysisData = {
  ticker: string;
  multiples: MultiplesData | null;
  montecarlo: MonteCarloData | null;
  research: ResearchData | null;
  newsSentiment: NewsSentimentItem[];
  overallNewsSentiment: OverallNewsSentiment[];
};

const API_BASE_URL = "http://127.0.0.1:8000";

async function fetchAnalysisForTicker(ticker: string): Promise<AnalysisData | null> {
  try {
    // Fetch all data in parallel
    const [
      multiplesResponse, 
      montecarloResponse, 
      researchResponse,
      newsSentimentResponse,
      overallNewsSentimentResponse
    ] = await Promise.all([
      fetch(`${API_BASE_URL}/multiples?ticker=${encodeURIComponent(ticker)}`),
      fetch(`${API_BASE_URL}/montecarlo?ticker=${encodeURIComponent(ticker)}`),
      fetch(`${API_BASE_URL}/research?ticker=${encodeURIComponent(ticker)}`),
      fetch(`${API_BASE_URL}/news-sentiment?ticker=${encodeURIComponent(ticker)}`),
      fetch(`${API_BASE_URL}/overall-news-sentiment?ticker=${encodeURIComponent(ticker)}`),
    ]);

    let multiples: MultiplesData | null = null;
    let montecarlo: MonteCarloData | null = null;
    let research: ResearchData | null = null;
    let newsSentiment: NewsSentimentItem[] = [];
    let overallNewsSentiment: OverallNewsSentiment | null = null;

    // Parse multiples data if successful
    if (multiplesResponse.ok) {
      multiples = await multiplesResponse.json();
    }

    // Parse monte carlo data if successful
    if (montecarloResponse.ok) {
      montecarlo = await montecarloResponse.json();
    }

    // Parse research data if successful
    if (researchResponse.ok) {
      research = await researchResponse.json();
    }

    // Parse news sentiment data if successful
    if (newsSentimentResponse.ok) {
      newsSentiment = await newsSentimentResponse.json();
    }

    // Parse overall news sentiment data if successful
    if (overallNewsSentimentResponse.ok) {
      overallNewsSentiment = await overallNewsSentimentResponse.json();
    }

    // Return analysis data even if one or more endpoints fail
    // This allows partial data to be displayed
    return {
      ticker: ticker.toUpperCase(),
      multiples,
      montecarlo,
      research,
      newsSentiment,
      overallNewsSentiment,
    };
  } catch (error) {
    console.error("Error fetching analysis data:", error);
    return null;
  }
}

const StockAnalysis = () => {
  // ✅ read the dynamic URL param :ticker
  const params = useParams<{ ticker?: string }>();
  const rawTicker = params.ticker;
  

  // guard: if URL does not include a ticker, send to 404
  if (!rawTicker) return <Navigate to="/not-found" replace />;

  // normalize (watch out for things like BRK.B → encode in links)
  const ticker = useMemo(() => rawTicker.toUpperCase(), [rawTicker]);

  const [openDetail, setOpenDetail] = useState<DetailType>(null);
  const [showComparePicker, setShowComparePicker] = useState(false);
  const [selectedComparisonTicker, setSelectedComparisonTicker] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  // load the analysis for the ticker from your store or backend
  useEffect(() => {
    let active = true;
    setLoading(true);
    setAnalysis(null);

    fetchAnalysisForTicker(ticker).then((res) => {
      if (!active) return;
      setAnalysis(res);
      console.log(res);
      setLoading(false);
    });

    return () => {
      active = false;
    };
  }, [ticker]);

  // initial prompt to pick a comparable
  useEffect(() => {
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

  // Mock data until backend wires sector peers
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
  };

  const detailContent = {
    relative: {
      title: "Relative Valuation",
      icon: <Scale className="h-6 w-6 text-primary" />,
      description: "Compare stocks using price multiples",
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Relative valuation helps you compare similar companies by looking at their price multiples.
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
            Much higher multiples than peers can mean overvaluation. Much lower can mean undervaluation or a risk discount.
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
            The DCF model estimates intrinsic value from future cash flows discounted to today.
          </p>
          <div className="bg-secondary/30 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">How It Works:</h4>
            <ol className="space-y-2 text-sm list-decimal list-inside">
              <li>Forecast cash flows</li>
              <li>Discount to present value</li>
              <li>Compare intrinsic value to market price</li>
            </ol>
          </div>
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
            Run many scenarios to see a distribution of possible future prices.
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
            Aggregate and score recent headlines for overall sentiment.
          </p>
        </div>
      ),
    },
  };

  // Loading and empty states tied to the dynamic ticker
  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-16 text-center text-muted-foreground">
          Loading analysis for {ticker}…
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-16 text-center">
          <h1 className="text-3xl font-semibold mb-2">{ticker}</h1>
          <p className="text-muted-foreground mb-6">
            No saved analysis found for {ticker}.
          </p>
          {/* Link to your analyze flow */}
          {/* <Link to={`/analyze?symbol=${encodeURIComponent(ticker)}`} className="underline">Run analysis now</Link> */}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-2">{ticker}</h1>
          <p className="text-muted-foreground">Comprehensive Stock Analysis</p>
        </div>
        
        <div className="mt-6 mb-10 flex justify-center">
            <AddToWatchlistButton ticker={ticker} />
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
                <div className="bg-secondary/30 p-4 rounded-lg mb-4 border-2 border-dashed border-red-400">
                  <div className="flex items-center gap-2 mb-2">
                    <ArrowRight className="h-5 w-5 text-red-600 animate-pulse" />
                    <p className="text-sm font-medium text-red-700">Action Required</p>
                  </div>
                  <p className="text-sm text-red-600">Select a comparable stock to begin analysis</p>
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
                <Button onClick={() => setShowComparePicker(true)} variant="outline" className="w-full">
                  {selectedComparisonTicker ? "Change Comparison Stock" : `Compare ${ticker} to Another Stock`}
                </Button>
                {selectedComparisonTicker && (
                  <Button onClick={() => setOpenDetail("relative")} className="w-full">
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
                <p className="text-sm text-muted-foreground">Intrinsic value calculation based on projected cash flows</p>
              </div>
              <Button onClick={() => setOpenDetail("absolute")} className="w-full">
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
                <p className="text-sm text-muted-foreground">Probability-based price projection analysis</p>
              </div>
              <Button onClick={() => setOpenDetail("montecarlo")} className="w-full">
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
                <p className="text-sm text-muted-foreground">Natural language processing of recent news articles</p>
              </div>
              <Button onClick={() => setOpenDetail("sentiment")} className="w-full">
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
            <SheetDescription>{openDetail && detailContent[openDetail].description}</SheetDescription>
          </SheetHeader>
          <div className="mt-6">{openDetail && detailContent[openDetail].content}</div>
        </SheetContent>
      </Sheet>

      {/* Comparison Stock Picker Sidebar */}
      <Sheet open={showComparePicker} onOpenChange={setShowComparePicker}>
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Select a Comparable Stock</SheetTitle>
            <SheetDescription>Choose from top 10 stocks in the same sector (S&P 500)</SheetDescription>
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

export default StockAnalysis;
