import { Link, useLocation, useNavigate } from "react-router-dom";
import { TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold">
            <TrendingUp className="h-6 w-6 text-primary" />
            <span>InvestoMommy</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-6">
            <Link 
              to={user ? "/dashboard" : "/login"}
              className={`transition-colors ${isActive('/dashboard') ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Dashboard
            </Link>
            <Link 
              to={user ? "/analyze" : "/login"}
              className={`transition-colors ${isActive('/analyze') ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Analyze Stock
            </Link>
            <Link 
              to="/disclaimer" 
              className={`transition-colors ${isActive('/disclaimer') ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Disclaimer
            </Link>
            <Link 
              to="/how-it-works" 
              className={`transition-colors ${isActive('/how-it-works') ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
            >
              How it Works
            </Link>
            <Link 
              to="/about" 
              className={`transition-colors ${isActive('/about') ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
            >
              About
            </Link>
          </div>
          
          {user ? (
            <Button 
              variant="default" 
              onClick={async () => {
                await signOut();
                navigate('/');
              }}
            >
              Log out
            </Button>
          ) : (
            <Link to="/login">
              <Button variant="default">Log in</Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
