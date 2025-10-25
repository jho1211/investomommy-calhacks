import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart3, TrendingUp, Users, Zap } from "lucide-react";
import Navigation from "@/components/Navigation";

const Home = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              Nurture Your <span className="text-primary">Investments</span> Like Your{" "}
              <span className="text-primary">Mother</span> Nurtures You
            </h1>
            <p className="text-lg text-muted-foreground mb-8">
              InvestoMommy helps you analyze stocks with AI-powered insights, track your portfolio, and make informed investment decisions.
            </p>
            <div className="flex gap-4">
              <Link to="/analyze">
                <Button size="lg">Get Started</Button>
              </Link>
              <Link to="/about">
                <Button size="lg" variant="outline">Learn More</Button>
              </Link>
            </div>
          </div>
          <div className="flex justify-center">
            <img 
              src="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=800&q=80" 
              alt="Investment growth concept"
              className="rounded-lg shadow-lg w-full max-w-md"
            />
          </div>
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="bg-secondary/30 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">
            Why Choose InvestoMommy?
          </h2>
          <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
            Our platform combines AI technology with comprehensive market data to give you the insights you need to assess stock valuations.
          </p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent className="pt-6 text-center">
                <BarChart3 className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2">AI-Powered Analysis</h3>
                <p className="text-muted-foreground">
                  Get detailed stock analysis powered by artificial intelligence and real-time market data.
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6 text-center">
                <TrendingUp className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2">Smart Insights</h3>
                <p className="text-muted-foreground">
                  Receive sentiment analysis on news and market trends to stay ahead of the curve.
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6 text-center">
                <Users className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2">Beginner-Friendly</h3>
                <p className="text-muted-foreground">
                  A clean, intuitive interface that makes stock analysis accessible to everyone — no finance degree required.
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6 text-center">
                <Zap className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2">Real-time Updates</h3>
                <p className="text-muted-foreground">
                  Access live market data and instant notifications for your portfolio.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
