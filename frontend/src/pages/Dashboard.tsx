import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/contexts/AuthContext";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Trash2, TrendingUp } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

type WatchlistItem = {
  ticker: string;
  company_name: string;
};
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";


/**
 * GETs the watchlist using query params:
 *   GET /userlist?uid=<user_id>
 */
async function fetchWatchlist(uid: string) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/userlist?uid=${encodeURIComponent(uid)}`
    ); 
    // If backend returns an error status (e.g., 400/500), stop here
    if (!response.ok) {
      throw new Error('HTTP ${response.status}');
    }
    
    // ex: [{ ticker: "AAPL", company_name: "Apple Inc." }, ...]
    return await response.json(); 
  } catch (error) {
    console.error("Error fetching watchlist:", error);
    return null;
  }
  
}

export default function Dashboard() {
  const { user } = useAuth(); // Get logged-in user from Supabase auth context
  const [watchlist, setWatchlist] = useState<WatchlistItem[] | null>(null); // Holds fetched data
  const [loading, setLoading] = useState(true); // UI state while loading
  const navigate = useNavigate();
  const { toast } = useToast();

  // Fetch watchlist as soon as `user` becomes available (i.e., once logged in)
  useEffect(() => {
    // If no user is logged in, stop loading and show login screen
    if (!user) {
      setLoading(false);
      return;
    }
    // Self-calling async function inside useEffect
    (async () => {
      const data = await fetchWatchlist(user.id); // Call our API
      if (!data) {
        // If fetching failed, show error 
        toast({
          title: "Error",
          description: "Failed to load watchlist",
          variant: "destructive",
        });
      }
      setWatchlist(data ?? []); // If `null`, default to empty array
      setLoading(false); // Stop loading animation
    })();
  }, [user, toast]);

  // If user is not logged in, show Login prompt instead
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5">
        <Navigation />
        <div className="container mx-auto px-4 py-16 text-center">
          <h1 className="text-3xl font-bold mb-4">Please Log In</h1>
          <p className="text-muted-foreground mb-8">
            You need to be logged in to view your watchlist
          </p>
          <Button onClick={() => navigate("/login")}>Go to Login</Button>
        </div>
      </div>
    );
  }
  // Main UI rendering
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5">
      <Navigation />
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">My Watchlist</h1>
          <p className="text-muted-foreground">
            Track and analyze your favorite stocks
          </p>
        </div>

        {/* Loading state */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading watchlist...</p>
          </div>
        ) : !watchlist || watchlist.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <TrendingUp className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold mb-2">No stocks in watchlist</h3>
              <p className="text-muted-foreground mb-6">
                Start by analyzing a stock and adding it to your watchlist
              </p>
              <Button onClick={() => navigate("/analyze")}>Analyze Stock</Button>
            </CardContent>
          </Card>
        ) : (
          // Render watchlist items
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {watchlist.map((item, idx) => (
              <Card key={`${item.ticker}-${idx}`} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="text-2xl font-bold">{item.ticker}</span>
                  </CardTitle>
                  <CardDescription>{item.company_name}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full" onClick={() => navigate(`/dashboard/analysis/${item.ticker}`)}>
                    Show Analysis
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}