## Our Inspiration
In an era where our community is hyper-fixated on building the next flashy AI or humanoid robot, we wanted to refocus our energy into building something that addresses a need that affects another community that hold great importance to us: our families.

Everyone on our team comes from an immigrant family, parents who traded a lifetime of hours and physical labor for income, working tirelessly to give us the opportunity to chase our dreams in achieving the "sexy" tech ventures everyone is focused on today. But in doing so, many never had the time, language skills, or resources to learn financial literacy to invest and build passive income. 

As children of immigrants, watching our parents struggle through job insecurity, rising living costs, and uncertainty in navigating the investment world inspired us to create InvestoMommy, a tool that lowers the barriers to investing, making the money that our families have worked so hard for, make money back for them. 

## What Our Service Offers
InvestoMommy brings professional-grade investment analysis to everyday users through five powerful features:
1. **Absolute Valuation (DCF)**: Estimate a company’s true worth by forecasting future cash flows and discounting them to present value.
2. **Relative Valuation (Price Multiples)**: Compare a stock’s metrics (eg P/E or EV/EBITDA) to industry peers to spot over- or undervaluation.
3. **Monte Carlo Simulation**: Model thousands of possible market scenarios to visualize risk, volatility, and probability-based price outcomes.
4. **News Sentiment Analysis**: Leverage FinBERT NLP to interpret financial headlines and measure how market sentiment affects a company’s outlook.
5. **Deep Dive Equity Research**: Access a comprehensive research dashboard that consolidates valuation models, company fundamentals, and sentiment trends—all in one place.

## TAM/SAM/SOM<br>
*Disclaimer: These figures are rough estimates that we plan to refine further with more accurate market research and user data.*
### Total Addressable Market (TAM)
- The global fintech market is worth around $340B and projected to reach $930B by 2030.
- Out of that, financial analytics and education tools make up about $50B in opportunity.
- There are over 500 million active retail investors worldwide who look for platforms that make market data easier to understand.<br>
**TAM = ~$50B**

### Serviceable Available Market (SAM)
Our first focus is North America. 
- North America makes up about **38%** of the fintech analytics space, or **~$19B**.
- Within that about **90 million people** fall into the group we can realistically reach who are trying to understand finance in a simple, interactive way. <br>
**SAM = ~$5-6B**

### Serviceable Obtainable Market (SOM) 
After talking with professionals from J.P. Morgan, Goldman Sachs, Baird, Morgan Stanley, Bank of America, Cresset and others we built a realistic market capture goal: 
- If we reach 1% of the North American segment (~900,000 users) at $5/month that’s $54M a year.
- A smaller achievable goal is 0.3% of that group (~270,000 users) which equals about $16M in annual revenue.
- These numbers reflect what’s possible in the next 3–5 years with steady growth and user adoption.<br>
**SOM = $16M - $54M (3-5 years)**

## How We Built It
**Research** <br>
1. Consulted equity researchers and executives at JP Morgan, Bank of America, and Morgan Stanley to understand strategies used for valuing businesses and stock prices.
2. Referred to industry-trusted resources to read financial documents (eg Investopedia, Yahoo Finance, and Warren Buffet).
3. Researched formulas, algorithms, and other quantitative/qualitative strategies used to assess stock value.

**Front End**<br>
- **Lovable** to create a skeleton of the front end.
- **React, TypeScript, TailwindCSS, and HTML/CSS** to further customize the front end to accommodate features we wanted to offer 
- **Supabase PostgreSQL** databases to save user authentication data, stock analyses data, and stock watchlists

**Back End**<br>
Python FastAPI that coded the following features: 
- **Relative Valuation** - Financial metrics pulled via FMP API, custom back end calculations for price multiples/ratios, PostgreSQL to save analyzed data for previously run stocks.
- **Absolute Valuation** - Python algorithm for DCF model written with Claude and financial metrics from Yahoo Finance and FMP API.
- **Monte Carlo Simulation** - One of our team members, a Junior Analyst at Montano Investment Fund, brought hands-on experience in designing Monte Carlo simulations, expertise that helped us model stock volatility and forecast valuation outcomes.
- **News Sentiment Analysis** - Extracting real-time headlines from the Finnhub API and running through FinBERT NLP model and Claude to quantify market sentiment and visualize how news impacts stock performance.

## Challenges We Ran Into
Some challenges we ran into are the following: 
- Accomplishing specific accuracy with the DCF model for valuing intrinsic value of stocks
- Navigating sentiment analyses of news articles related to stocks, and deciding which qualitative data to extract

## What's Next for Us
To honor one of our core values at InvestoMommy, **accessibility**, we plan on implementing these additional features to make our product more accessible for people of different demographics and skill sets. 
1. Translating the application UI, explanation of finance terms, LLM-sentiment analysis of news headlines, and explanation of calculations to the next two most common languages spoken in the US, according to the [United States Census Bureau](https://www.census.gov/library/stories/2022/12/languages-we-speak-in-united-states.html): Spanish and Chinese.
2. Liaise with equity researchers and investment bankers to fine-tune the DCF model to improve accuracy of intrinsic valuations of companies.
3. Integrate brokerage app connections, allowing users to link their investment accounts directly to InvestoMommy so users can analyze potential stocks and make informed investment decisions with the ease of a few clicks.   

We envision a future where InvestoMommy can empower beginner-investors, like our immigrant families, to learn about stock investing and eventually build sustainable wealth.
