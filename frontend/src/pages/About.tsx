import Navigation from "@/components/Navigation";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Accessibility, BookCheck, Heart, User } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import jinaPhoto from "@/assets/headshots/jina.png";
import jeffreyPhoto from "@/assets/headshots/jeffrey.png";
import wehbePhoto from "@/assets/headshots/wehbe.png";
import farrukhPhoto from "@/assets/headshots/farrukh.png"

const About = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-center mb-4">About InvestoMommy</h1>
          <p className="text-center text-muted-foreground mb-12">
            Get to learn more about us.
          </p>

          <Card className="mb-12">
            <CardContent className="pt-8">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-bold">Our Mission</h2>
              </div>
              <p className="text-lg">
                To lower the barriers for beginner investors and to empower investors to take their first steps 
                into investing and building their wealth through passive income.
              </p>
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <Card>
              <CardContent className="pt-6 text-center">
                <Accessibility className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2">Accessibility</h3>
                <p className="text-muted-foreground">
                  Everyone deserves the tools to understand and participate in building wealth, regardless of their background, education, or financial literacy.
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6 text-center">
                <BookCheck className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2">Transparency</h3>
                <p className="text-muted-foreground">
                  Trust is earned through openness. We show our work so you can make informed decisions with confidence.
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6 text-center">
                <Heart className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="font-bold text-xl mb-2">Empowerment</h3>
                <p className="text-muted-foreground">
                  This platform doesn't tell you what to think. It gives you the information and clarity to decide for yourself.
                </p>
              </CardContent>
            </Card>
          </div>

          <Card className="mb-12">
            <CardContent className="pt-8">
              <h2 className="text-2xl font-bold text-center mb-8">Meet the Team</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                <div className="flex flex-col items-center">
                  <Avatar className="h-24 w-24 mb-4">
                    <AvatarImage src={jinaPhoto} alt="Jina Yeom Headshot" />
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                      <User className="h-12 w-12" />
                    </AvatarFallback>
                  </Avatar>
                  <p className="font-medium text-center">Jina Yeom</p>
                </div>

                <div className="flex flex-col items-center">
                  <Avatar className="h-24 w-24 mb-4">
                    <AvatarImage src={jeffreyPhoto} alt="Jeffrey Ho Headshot" />
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                      <User className="h-12 w-12" />
                    </AvatarFallback>
                  </Avatar>
                  <p className="font-medium text-center">Jeffrey Ho</p>
                </div>

                <div className="flex flex-col items-center">
                  <Avatar className="h-24 w-24 mb-4">
                    <AvatarImage src={wehbePhoto} alt="Wehbe El Hadj Sidi Headshot" />
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                      <User className="h-12 w-12" />
                    </AvatarFallback>
                  </Avatar>
                  <p className="font-medium text-center">Wehbe El Hadj Sidi</p>
                </div>

                <div className="flex flex-col items-center">
                  <Avatar className="h-24 w-24 mb-4">
                    <AvatarImage src={farrukhPhoto} alt="Farrukh Akhatjonov Headshot" />
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                      <User className="h-12 w-12" />
                    </AvatarFallback>
                  </Avatar>
                  <p className="font-medium text-center">Farrukh Akhatjonov</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-8">
              <h2 className="text-2xl font-bold mb-4">Our Story</h2>
              <div className="space-y-4 text-muted-foreground">
                <p>
                  In an era where our community is hyper-fixated on building the next flashy AI or humanoid robot, 
                  we wanted to refocus our energy into building something that addresses a need that affects another 
                  community that hold great importance to us: our families. Everyone on our team comes from an immigrant 
                  family, parents who traded a lifetime of hours and physical labor for income, working tirelessly to give 
                  us the opportunity to chase our dreams in achieving the "sexy" tech ventures everyone is focused on today. 
                  But in doing so, many never had the time, language skills, or resources to learn financial literacy to invest 
                  and build passive income. 
                </p>
                <p>
                  As children of immigrants, watching our parents struggle through job insecurity, rising living costs, and uncertainty 
                  in navigating the investment world inspired us to create InvestoMommy, a tool that lowers the barriers to investing, 
                  making the money that our families have worked so hard for, make money back for them. 
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default About;
