import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Adjust this if you already centralize API config
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

type DcfResponse = {
  valuation?: {
    base_constant_wacc?: {
      intrinsic_value_per_share?: number | null;
      enterprise_value?: number | null;
      pv_of_terminal_value?: number | null;
    };
    dynamic_wacc?: {
      intrinsic_value_per_share?: number | null;
    };
  };
  assumptions?: {
    wacc_base?: number | null;
    terminal_growth_used?: number | null;
  };
  financials_snapshot?: {
    totals?: {
      price?: number | null;
    };
  };
};

function usd(n?: number | null) {
  if (n == null || isNaN(n)) return "—";
  return `$${n.toFixed(2)}`;
}
function pct(n?: number | null) {
  if (n == null || isNaN(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

async function fetchDcf(ticker: string): Promise<DcfResponse> {
  const url = `${API_BASE_URL}/api/dcf/${encodeURIComponent(ticker)}?years=10&midyear=true`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`DCF fetch failed: ${res.status}`);
  return res.json();
}

export default function DCF({ ticker }: { ticker: string }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dcf", ticker],
    queryFn: () => fetchDcf(ticker),
    staleTime: 1000 * 60, // 1 min
  });

  const {
    price,
    ivBase,
    ivDyn,
    wacc,
    tg,
    upsideBase,
    upsideDyn,
  } = useMemo(() => {
    const price = data?.financials_snapshot?.totals?.price ?? null;
    const ivBase = data?.valuation?.base_constant_wacc?.intrinsic_value_per_share ?? null;
    const ivDyn = data?.valuation?.dynamic_wacc?.intrinsic_value_per_share ?? null;
    const wacc = data?.assumptions?.wacc_base ?? null;
    const tg = data?.assumptions?.terminal_growth_used ?? null;

    const upsideBase =
      price != null && ivBase != null ? (ivBase - price) / price : null;
    const upsideDyn =
      price != null && ivDyn != null ? (ivDyn - price) / price : null;

    return { price, ivBase, ivDyn, wacc, tg, upsideBase, upsideDyn };
  }, [data]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DCF — Intrinsic Value</CardTitle>
          <CardDescription>Loading valuation…</CardDescription>
        </CardHeader>
        <CardContent className="text-muted-foreground text-sm">Fetching DCF numbers for {ticker}.</CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>DCF — Intrinsic Value</CardTitle>
          <CardDescription className="text-destructive">
            {(error as Error)?.message ?? "Failed to load"}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Check that the DCF server is running and CORS is allowed for your frontend origin.
        </CardContent>
      </Card>
    );
  }

  // Color tags for quick read
  const upClass = (u?: number | null) =>
    u == null
      ? "bg-muted text-foreground"
      : u >= 0
      ? "bg-emerald-600/15 text-emerald-600"
      : "bg-red-600/15 text-red-600";

  return (
    <Card>
      <CardHeader>
        <CardTitle>DCF — Intrinsic Value</CardTitle>
        <CardDescription className="text-muted-foreground">
          {ticker.toUpperCase()} • WACC {pct(wacc)} • g {pct(tg)}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Market price */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Market price</span>
          <span className="font-medium">{usd(price)}</span>
        </div>

        {/* Base intrinsic value */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Intrinsic value (Base)</span>
            <Badge className={upClass(upsideBase)}>
              {upsideBase == null ? "—" : `${(upsideBase * 100).toFixed(1)}%`}
            </Badge>
          </div>
          <span className="font-semibold">{usd(ivBase)}</span>
        </div>

        {/* Dynamic intrinsic value */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Intrinsic value (Dynamic)</span>
            <Badge className={upClass(upsideDyn)}>
              {upsideDyn == null ? "—" : `${(upsideDyn * 100).toFixed(1)}%`}
            </Badge>
          </div>
          <span className="font-semibold">{usd(ivDyn)}</span>
        </div>

        <p className="text-xs text-muted-foreground pt-2">
          Intrinsic values are derived from FCFF with a terminal growth model. Numbers are estimates and not investment advice.
        </p>
      </CardContent>
    </Card>
  );
}
