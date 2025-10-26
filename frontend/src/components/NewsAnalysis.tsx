// src/components/NewsAnalysis.tsx
import React, { useState } from "react";
import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";

ChartJS.register(ArcElement, Tooltip, Legend);

export type NewsItem = {
  id: number;
  headline: string;
  url: string;
  sentiment: "positive" | "negative" | "neutral";
  summary?: string | null;
  confidence?: number; 
};

interface NewsAnalysisProps {
  overallNewsSentiment: {
    positive_ratio: number;
    neutral_ratio: number;
    negative_ratio: number;
    total_articles?: number;
    date?: string;
  };
  newsSentiment?: NewsItem[];
}

const clamp = (v?: number) =>
  Number.isFinite(v!) ? Math.max(0, Math.min(1, v!)) : 0;

const pctWidth = (v?: number) =>
  `${Math.max(0, Math.min(1, v ?? 0)) * 100}%`;

const sentimentBadgeClass = (s: "positive" | "neutral" | "negative") =>
  s === "positive"
    ? "bg-emerald-100 border-emerald-300"
    : s === "negative"
    ? "bg-red-100 border-red-300"
    : "bg-yellow-100 border-yellow-300";


const NewsAnalysis: React.FC<NewsAnalysisProps> = ({
  overallNewsSentiment,
  newsSentiment = [],
}) => {
  const [openModal, setOpenModal] = useState(false);

  const pos = clamp(overallNewsSentiment?.positive_ratio);
  const neu = clamp(overallNewsSentiment?.neutral_ratio);
  const neg = clamp(overallNewsSentiment?.negative_ratio);

  const data = {
    labels: ["Positive", "Neutral", "Negative"],
    datasets: [
      {
        data: [pos * 100, neu * 100, neg * 100],
        backgroundColor: ["#10B981", "#FACC15", "red"],
        borderColor: "#fff",
        borderWidth: 2,
        hoverOffset: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false as const,
    plugins: {
      legend: { position: "bottom" as const },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `${ctx.label}: ${ctx.parsed.toFixed(0)}%`,
        },
      },
    },
  };

  return (
    <div className="space-y-4">
      {/* Pie chart */}
      <div className="h-64">
        <Pie data={data} options={options} />
      </div>
    {/* Summary Strip (ratios + stacked bar) */}
    <div className="bg-secondary/30 p-4 rounded-lg">
    <div className="flex items-center justify-between text-sm mb-3">
        <span className="text-muted-foreground">
        {overallNewsSentiment.date ?? ""}
        {typeof overallNewsSentiment.total_articles === "number"
            ? ` • ${overallNewsSentiment.total_articles} articles`
            : ""}
        </span>
        <div className="flex gap-2 font-medium">
        <span className="text-emerald-600">{(pos * 100).toFixed(0)}% pos</span>
        <span className="text-yellow-500">{(neu * 100).toFixed(0)}% neu</span>
        <span className="text-red-600">{(neg * 100).toFixed(0)}% neg</span>
        </div>
    </div>

    <div className="w-full h-2 rounded bg-muted overflow-hidden flex">
        <div className="h-2 bg-emerald-500" style={{ width: pctWidth(pos) }} />
        <div className="h-2 bg-yellow-400" style={{ width: pctWidth(neu) }} />
        <div className="h-2 bg-red-500" style={{ width: pctWidth(neg) }} />
    </div>
    </div>


      {/* Right-aligned, small, green-outline button */}
      <div className="flex justify-end">
        <Button
          onClick={() => setOpenModal(true)}
          variant="outline"
          className="border-[#10B981] text-[#10B981] hover:bg-[#10B981]/10 text-sm px-3 py-1.5"
        >
          Read News Headlines
        </Button>
      </div>

      {/* Modal (overlay) with headlines */}
      <Dialog open={openModal} onOpenChange={setOpenModal}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Recent News Headlines</DialogTitle>
            <DialogDescription>
              Click any headline to open it in a new tab.
            </DialogDescription>
          </DialogHeader>

            <div className="mt-2 space-y-2">
                {newsSentiment.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No news available.</p>
                ) : (
                    newsSentiment.map((item) => (
                    <Card key={item.id} className="bg-background/50">
                        <CardContent className="pt-4">
                        <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-primary hover:underline"
                        >
                            {item.headline}
                        </a>
                        <p className="text-sm mt-1">
                            <span className="text-muted-foreground">Sentiment: </span>
                            <span
                            className={`
                                inline-flex items-center gap-1 px-2 py-0.5 rounded-md border
                                ${sentimentBadgeClass(item.sentiment)}
                            `}
                            >
                            <span className="capitalize text-xs font-semibold text-black">
                                {item.sentiment}
                            </span>
                            </span>
                        </p>

                        {item.summary && (
                            <p className="text-sm mt-2">{item.summary}</p>
                        )}
                        </CardContent>
                    </Card>
                    ))
                )}
                </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default NewsAnalysis;
