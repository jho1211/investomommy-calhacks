import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Star } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AddToWatchlistButtonProps {
  ticker: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function addToWatchlist(uid: string, ticker: string): Promise<boolean> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/userlist?uid=${encodeURIComponent(uid)}&ticker=${encodeURIComponent(
        ticker.toUpperCase()
      )}`,
      { method: "POST" } // no body needed if FastAPI is reading from query params
    );

    return response.ok;
  } catch (error) {
    console.error("Error adding to watchlist:", error);
    return false;
  }
}

const AddToWatchlistButton = ({ ticker }: AddToWatchlistButtonProps) => {
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();

  const handleAddToWatchlist = async () => {
    if (!user) {
      toast({
        title: "Not logged in",
        description: "Please log in to add stocks to your watchlist.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    const ok = await addToWatchlist(user.id, ticker);
    setLoading(false);

    if (ok) {
      toast({
        title: "Added to watchlist",
        description: `${ticker.toUpperCase()} has been added to your watchlist.`,
      });
    } else {
      toast({
        title: "Error",
        description: "Could not add to watchlist.",
        variant: "destructive",
      });
    }
  };

  return (
    <Button
      onClick={handleAddToWatchlist}
      disabled={loading}
      variant="outline"
      className="gap-2"
    >
      <Star className="h-4 w-4" />
      {loading ? "Adding..." : "Add to Watchlist"}
    </Button>
  );
};

export default AddToWatchlistButton;
