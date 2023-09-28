# Publishing your blog

## Cloudflare Pages

1. Create your project  
 From your [dashboard](https://dash.cloudflare.com), select the *Workers & Pages* section.  
 Click the *Create application* button.  
 Select *Pages* then click the *Connect to Git* button.  
 Configure your account, select your blog repository.  

2. Set your project settings  
**Build command:** `pip install gitblog2 && gitblog2 -l debug`  
**Build output directory:** /public  
**Build system version:** 2 (latest)  
**Root directory:** /  
**Environment variables:**

| Variable name    | Value                 |
| ----------- | ------------------------------------ |
| BASE_URL         | `https://your-blog.com` |
| GITHUB_TOKEN    | YOUR_API_TOKEN        |
| PYTHON_VERSION  | 3.11                  |
