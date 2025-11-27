# Page snapshot

```yaml
- generic [ref=e2]:
  - img "Kibray Logo" [ref=e3]
  - heading "Welcome Back" [level=2] [ref=e4]
  - paragraph [ref=e5]: Sign in to continue to Kibray
  - generic [ref=e6]:
    - generic [ref=e7]:
      - generic [ref=e8]:
        - generic [ref=e9]: 
        - text: Username
      - generic [ref=e10]: 
      - textbox " Username" [active] [ref=e11]
    - generic [ref=e12]:
      - generic [ref=e13]:
        - generic [ref=e14]: 
        - text: Password
      - generic [ref=e15]: 
      - textbox " Password" [ref=e16]
    - button " Sign In" [ref=e17] [cursor=pointer]:
      - generic [ref=e18]: 
      - text: Sign In
  - generic [ref=e19]:
    - text: "Language:"
    - link "English" [ref=e20] [cursor=pointer]:
      - /url: "?lang=en"
    - link "Español" [ref=e21] [cursor=pointer]:
      - /url: "?lang=es"
```