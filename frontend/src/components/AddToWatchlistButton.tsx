import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Star } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AddToWatchlistButtonProps {
  ticker: string;
}

const AddToWatchlistButton = ({ ticker }: AddToWatchlistButtonProps) => {
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();

  const handleAddToWatchlist = async () => {
    if (!user) {
      toast({
        title: "Not logged in",
        description: "Please log in to add stocks to your watchlist",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const { error } = await supabase
        .from("userticker")
        .insert({
          user_id: user.id,
          ticker: ticker.toUpperCase(),
        });

      if (error) {
        if (error.code === "23505") {
          toast({
            title: "Already in watchlist",
            description: `${ticker} is already in your watchlist`,
          });
        } else {
          throw error;
        }
      } else {
        toast({
          title: "Added to watchlist",
          description: `${ticker} has been added to your watchlist`,
        });
      }
    } catch (error) {
      console.error("Error adding to watchlist:", error);
      toast({
        title: "Error",
        description: "Failed to add stock to watchlist",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
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
