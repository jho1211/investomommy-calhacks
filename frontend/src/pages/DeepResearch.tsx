import { useEffect, useMemo, useState } from "react";
import { useParams, Link, Navigate } from "react-router-dom";
import Navigation from "@/components/Navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Newspaper } from "lucide-react";

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

const API_BASE_URL = "http://127.0.0.1:8000";

export default function DeepResearch() {
  const params = useParams<{ ticker?: string }>();
  const rawTicker = params.ticker;
  const ticker = useMemo(() => (rawTicker ? rawTicker.toUpperCase() : ""), [rawTicker]);

  const [loading, setLoading] = useState(true);
  const [research, setResearch] = useState<ResearchData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  if (!rawTicker) return <Navigate to="/not-found" replace />;

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setResearch(null);

    const url = `${API_BASE_URL}/research?ticker=${encodeURIComponent(ticker)}`;

    fetch(url)
      .then(async (r) => {
        if (!r.ok) {
          const t = await r.text();
          throw new Error(t || `Request failed (${r.status})`);
        }
        return r.json();
      })
      .then((json: ResearchData) => {
        if (!active) return;
        setResearch(json);
      })
      .catch((e) => {
        if (!active) return;
        console.error(e);
        setError(e.message || "Failed to fetch deep research.");
        toast({
          title: "Deep research failed",
          description: "Could not load research from the backend.",
          variant: "destructive",
        });
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [ticker, toast]);

  const renderSection = (title: string, items?: string[]) => {
    if (!items || items.length === 0) return null;
    return (
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription className="text-muted-foreground">
            Key points summarized for {ticker}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            {items.map((line, idx) => (
              <li key={idx}>{line}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold">{ticker} — Deep Research</h1>
            <p className="text-muted-foreground">LLM-assisted equity research from your backend</p>
          </div>
          <Badge variant="secondary" className="gap-2">
            <Newspaper className="h-4 w-4" />
            Equity Research
          </Badge>
        </div>

        {loading && (
          <div className="text-center text-muted-foreground py-20">Loading deep research for {ticker}…</div>
        )}

        {!loading && error && (
          <div className="text-center text-red-600 py-20">
            <p className="font-medium mb-2">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {!loading && research && (
          <div className="grid md:grid-cols-2 gap-6">
            {renderSection("Company Overview", research.analysis_data.company_overview)}
            {renderSection("Business Segments", research.analysis_data.business_segments)}
            {renderSection("Revenue Characteristics", research.analysis_data.revenue_characteristics)}
            {renderSection("Geographic Breakdown", research.analysis_data.geographic_breakdown)}
            {renderSection("Stakeholders", research.analysis_data.stakeholders)}
            {renderSection("Key Performance Indicators (KPIs)", research.analysis_data.key_performance_indicators)}
            {renderSection("Valuation Notes", research.analysis_data.valuation)}
            {renderSection("Recent News Highlights", research.analysis_data.recent_news)}
            {renderSection("Forensic Red Flags", research.analysis_data.forensic_red_flags)}
          </div>
        )}

        <div className="mt-10 flex gap-3">
          <Button asChild variant="outline">
            <Link to={`/dashboard/analysis/${encodeURIComponent(ticker)}`}>Back to Analysis</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
