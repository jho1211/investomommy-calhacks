// src/pages/StockAnalysis.tsx
import { useParams, Navigate, Link } from "react-router-dom";
import { useState, useEffect, useMemo } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Scale, TrendingUp, BarChart3, Newspaper, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import AddToWatchlistButton from "@/components/AddToWatchlistButton";
import { MonteCarloChart } from "@/components/MonteCarloChart";
import NewsAnalysis from "@/components/NewsAnalysis";

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
  overallNewsSentiment: OverallNewsSentiment;
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
      fetch(`${API_BASE_URL}/api/research?ticker=${encodeURIComponent(ticker)}`),
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
  // Read the dynamic URL param :ticker
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
          <h4 className="font-semibold mb-2">Purpose:</h4>
          <p className="text-muted-foreground">
            Compare a company’s market value to peers in the same industry to gauge whether it’s trading at a premium 
            or discount based on key financial ratios.
          </p>

          <h4 className="font-semibold mb-2">Overview:</h4>
          <p className="text-muted-foreground">
            Higher valuation multiples suggest investors expect stronger growth, while lower multiples can signal undervaluation 
            or weaker prospects. However, these comparisons are only meaningful between companies with similar business models, 
            sizes, and profit margins.
          </p>
          <p className="text-muted-foreground">Below are the price multiples that were used to compare the companies with their peers of your choice.</p>
          
          {/* EV/EBITDA */}
          <h4 className="font-semibold mb-2">EV/EBITDA:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: How many dollars of total company value (EV) investors pay for each $1 of operating profit before 
              interest, taxes, depreciation, and amortization.
          </p>
          <p className="text-muted-foreground"><strong>Interpretation</strong>: </p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>Higher Multiple</strong> - Investors expect faster growth, higher margins, or see it as a higher-quality business.</li>
            <li><strong>Lower Multiple</strong> - The company may be cheaper, riskier, or growing slower.</li>
          </ul>

          {/* EV/FCF */}
          <h4 className="font-semibold mb-2">EV/FCF (Free Cash Flow):</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: How many dollars of total value investors pay for each $1 of free cash flow.</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>Higher EV/FCF</strong> - Market expects future cash flow growth or sees it as a high-quality generator.</li>
            <li><strong>Lower EV/FCF</strong> - Could be undervalued or have low confidence in cash flow sustainability.</li>
          </ul>

          {/* EV/Sales */}
          <h4 className="font-semibold mb-2">EV/Sales:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: How many dollars of total company value investors pay for each $1 of sales.</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>Higher EV/Sales</strong> - Often means strong margins or rapid growth expected.</li>
            <li><strong>Lower EV/Sales</strong> - May indicate low profitability or slower growth.</li>
          </ul>

          {/* EV/Revenue per Employee */}
          <h4 className="font-semibold mb-2">EV/Revenue per Employee:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: The total company value per employee, showing how efficiently a company generates value with its workforce.</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>Higher ratio</strong> - More productive workforce or higher automation.</li>
            <li><strong>Lower ratio</strong> - Labor-intensive or inefficient operations.</li>
          </ul>

          {/* Price/Book Value */}
          <h4 className="font-semibold mb-2">Price / Book Value:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: How much investors pay relative to the company’s net assets (assets − liabilities).</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>Higher P/B</strong> - Investors believe the company earns strong returns on assets or has valuable intangibles (like brand or tech).</li>
            <li><strong>Lower P/B</strong> - Could signal undervaluation or poor asset returns.</li>
          </ul>

          {/* Debt/Equity Value */}
          <h4 className="font-semibold mb-2">Debt / Equity:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: How much debt the company uses relative to shareholders’ equity.</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>Higher D/E</strong> - More financial risk, but can amplify returns.</li>
            <li><strong>Lower D/E</strong> - More conservative, safer balance sheet.</li>
          </ul>

          {/* EV/Invested Capital*/}
          <h4 className="font-semibold mb-2">EV / Invested Capital:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: Compares total company value to all capital invested (debt + equity − cash).
          Example: A = 1.5×, B = 3.0× → B is more expensive; investors value its capital base higher.</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>EV/Invested Capital &gt; 1</strong> - Company creates value above cost of capital.</li>
            <li><strong>EV/Invested Capital &lt; 1</strong> - Company may be destroying value or underperforming.</li>
          </ul>

          {/* P/E */}
          <h4 className="font-semibold mb-2">Price / Earnings:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: How many dollars investors pay for each $1 of earnings (profit).</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>High P/E</strong> - Market expects strong profit growth.</li>
            <li><strong>Low P/E</strong> - Company may be undervalued, mature, or risky.</li>
          </ul>

          {/* EV/EBITD */}
          <h4 className="font-semibold mb-2">EV/EBITD:</h4>
          <p className="text-muted-foreground"><strong>Meaning</strong>: How many dollars of total company value investors pay for each $1 of EBIT (earnings before interest and taxes).</p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li><strong>High EV/EBITD</strong> - Investors expect high growth or returns.</li>
            <li><strong>Low EV/EBITD</strong> - Might be cheaper, or facing lower growth or operational risks.</li>
          </ul>
        </div>
      ),
    },
    absolute: {
      title: "Absolute Valuation (DCF Model)",
      icon: <TrendingUp className="h-6 w-6 text-primary" />,
      description: "Determine intrinsic stock value",
      content: (
        <div className="space-y-4">
          <h4 className="font-semibold mb-2">Purpose:</h4>
          <p className="text-muted-foreground">
            Find what a company is really worth, not just what the market says.
          </p>

          <h4 className="font-semibold mb-2">Overview:</h4>
          <p className="text-muted-foreground">
            The <strong>Discounted Cash Flow (DCF)</strong> model helps estimate a company’s true or “intrinsic” value. 
            It does this by predicting how much cash the business will make in the future and then 
            converting those future amounts into what they’re worth today. This helps investors decide 
            if a stock is overpriced or a good deal.
          </p>

          <h4 className="font-semibold mb-2">How It Works:</h4>
          <ol className="text-muted-foreground list-decimal list-inside">
            <li><strong>Forecast future cash flows</strong> – Estimate how much money the company will generate each year.</li>
            <li><strong>Discount to present value</strong> - Use a discount rate to adjust for risk and the fact that money today is worth more than money in the future.</li>
            <li><strong>Find intrinsic value</strong> - Add up all those present values to get the company’s total worth.</li>
            <li><strong>Compare to market price</strong> – If the intrinsic value is higher than the current stock price, the stock might be undervalued.</li>
          </ol>
        </div>
      ),
    },
    montecarlo: {
      title: "Monte Carlo Simulation",
      icon: <BarChart3 className="h-6 w-6 text-primary" />,
      description: "Visualize price uncertainty",
      content: (
        <div className="space-y-4">
          <h4 className="font-semibold mb-2">Purpose:</h4>
          <p className="text-muted-foreground">
            Run many scenarios to visualize uncertainty and understand the 
            range of possible future stock prices.
          </p>

          <h4 className="font-semibold mb-2">Overview:</h4>
          <p className="text-muted-foreground">
            The <strong>Monte Carlo Simulation</strong> helps estimate how a company’s stock price might change 
            over time by running thousands of random scenarios based on past data. It doesn’t predict 
            the exact future but shows a range of possible outcomes and how likely each one is. This 
            helps investors see potential risks and returns under different market conditions.
          </p>
          
          <h4 className="font-semibold mb-2">How It Works::</h4>
          <ol className="space-y-2 text-muted-foreground list-decimal list-inside">
              <li><strong>Collect data</strong> – Use historical stock prices to understand how the stock usually moves.</li>
              <li><strong>Generate random paths</strong> - Simulate thousands of possible price paths using mathematical models.</li>
              <li><strong>Plot results</strong> - Create a graph showing all possible future prices to visualize uncertainty and volatility.</li>
              <li><strong>Interpret outcomes</strong> – A wider spread of results means higher risk, while a tighter range suggests more stability.</li>
            </ol>
          
          <h4 className="font-semibold mb-2">Line Graph:</h4>
          <p className="text-muted-foreground">
            The line graph displays many possible stock price paths over time. Each line starts at the same point and then moves 
            differently, spreading wider as time passes. This spread shows how volatility creates a range of possible outcomes.
          </p>

          <h4 className="font-semibold mb-2">Histogram:</h4>
          <p className="text-muted-foreground">
            The bar graph shows how often different final stock prices appeared after many simulations. The y-axis labeled 
            “frequency” represents how many times the final price landed in each range, meaning how common that outcome was. Taller 
            bars mean those prices occurred more frequently, forming a central peak where most outcomes landed. The right-leaning 
            shape means a few higher prices happened, but they were rare.
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
          <h4 className="font-semibold mb-2">Purpose:</h4>
          <p className="text-muted-foreground">
            Understand how news affects investor behavior and how market 
            tone can impact a company’s stock price.
          </p>

          <h4 className="font-semibold mb-2">Overview:</h4>
          <p className="text-muted-foreground">
            This tool uses AI to analyze recent financial news headlines about a company and 
            determine the overall sentiment. Each headline is classified as positive, negative, 
            or neutral, helping investors see how the market feels toward a company at a glance. 
            By tracking sentiment over time, you can spot patterns like growing optimism before 
            price jumps or negative tone before selloffs.
          </p>

          <h4 className="font-semibold mb-2">Why It Matters:</h4>
          <p className="text-muted-foreground">
            News moves markets. Understanding sentiment gives investors an early look at how perception is 
            shifting before it shows up in the price.
          </p>
          
          <h4 className="font-semibold mb-2">How It Works:</h4>
          <ol className="space-y-2 text-muted-foreground list-decimal list-inside">
              <li><strong>Collect news data</strong> – Collect news data – Using Finnhub to gather recent company-specific articles and headlines.</li>
              <li><strong>Analyze tone</strong> - Run each headline through FinBERT that detects whether the language is positive, negative, or neutral.</li>
              <li><strong>Investment sentiment</strong> - Assign a score between –1.0 and +1.0, where higher means more positive tone.</li>
              <li><strong>Summarize results</strong> – Combine the scores to find the overall market mood and visualize sentiment trends over time.</li>
              <li><strong>Interpret findings</strong> – A rising sentiment score could mean investors are more confident, while a drop might signal growing caution.</li>
            </ol>
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
// percent formatter: 0.42 -> "42%"
const toPct0 = (v?: number | null) =>
  v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`;

// choose a badge look based on sentiment
const sentimentBadgeClass = (s: "positive" | "neutral" | "negative") => {
  if (s === "positive") return "bg-emerald-100 text-emerald-700 border border-emerald-200";
  if (s === "negative") return "bg-red-100 text-red-700 border border-red-200";
  return "bg-slate-100 text-slate-700 border border-slate-200";
};

// tiny "time ago" formatter
const timeAgo = (iso: string) => {
  const d = new Date(iso);
  const s = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000));
  const mins = Math.floor(s / 60);
  const hrs = Math.floor(mins / 60);
  const days = Math.floor(hrs / 24);
  if (s < 60) return `${s}s ago`;
  if (mins < 60) return `${mins}m ago`;
  if (hrs < 24) return `${hrs}h ago`;
  return `${days}d ago`;
};

// extract host from a URL for display
const hostOf = (url: string) => {
  try { return new URL(url).host.replace(/^www\./, ""); } catch { return ""; }
};

// clamp a number (0–1) to percentage width for bars
const pctWidth = (v?: number | null) => {
  if (v === null || v === undefined || Number.isNaN(v)) return "0%";
  const clamped = Math.max(0, Math.min(1, v));
  return `${clamped * 100}%`;
};

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

            <CardContent className="space-y-4">
              {analysis?.montecarlo?.paths_url ? (
                <div className="bg-secondary/30 p-4 rounded-lg">
                  <MonteCarloChart data={analysis.montecarlo} />
                </div>
              ) : (
                <div className="bg-secondary/30 p-6 rounded-lg text-sm text-muted-foreground">
                  No Monte Carlo visualization available.
                </div>
              )}

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
                        
            <CardContent className="space-y-4">
              {/* Pie chart */}
              {analysis?.overallNewsSentiment ? (
                <div className="min-h-[280px]">
                  <NewsAnalysis
                    overallNewsSentiment={analysis.overallNewsSentiment}
                    newsSentiment={analysis.newsSentiment}
                  />
                </div>
              ) : (
                <div className="bg-secondary/30 p-4 rounded-lg text-sm text-muted-foreground">
                  No daily sentiment summary available.
                </div>
              )}

              <Button onClick={() => setOpenDetail("sentiment")} className="w-full">View Details</Button>
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
      {/* Deep Research CTA (bottom of the insight cards) */}
        <div className="max-w-5xl mx-auto mt-6">
          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="py-6">
              <div className="flex flex-col items-center gap-3">
                <p className="text-muted-foreground text-center">
                  Want to go deeper? Run our LLM-assisted equity research for {ticker}.
                </p>
                <Button asChild>
                  <Link to={`/research/${encodeURIComponent(ticker)}`}>Deep Research</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
    </div>
  );
};

export default StockAnalysis;
