import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Star } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import api from "@/lib/api";

interface AddToWatchlistButtonProps {
  ticker: string;
}

async function addToWatchlist(uid: string, ticker: string): Promise<boolean> {
  try {
    // Using axios - it automatically includes the Bearer token via interceptor
    await api.post(`/userlist`, null, {
      params: { 
        uid, 
        ticker: ticker.toUpperCase() 
      }
    });
    return true;
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
