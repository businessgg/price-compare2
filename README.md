# Price Comparison Tool

Aapki Shopify store aur competitor website ke products/prices ko har ghante
automatically compare karta hai, aur ek live dashboard (webpage) pe dikhata hai.

## Setup (ek dafa karna hai)

### 1. GitHub par naya repository banayein
- github.com par login karein
- "New repository" par click karein
- Naam dein (e.g. `price-compare`)
- **Public** rakhein (GitHub Pages free tier ke liye zaroori hai)
- "Create repository" par click karein

### 2. Ye saari files us repository mein upload karein
Is folder ki poori structure (jaisi hai waisi) GitHub par upload kar dein
("Add file" → "Upload files" button se, ya drag-drop kar ke), including:
- `config.json`
- `scripts/` folder (3 files)
- `.github/workflows/update.yml`
- `docs/index.html`
- `requirements.txt`

### 3. `config.json` mein apne URLs daalein
File ko GitHub par open karein, pencil (edit) icon par click karein, aur:
```json
"my_store": { "url": "yourstore.myshopify.com" },
"competitor": { "url": "https://competitor-website.com/shop" }
```
daal kar "Commit changes" karein.

**Note:** Agar competitor site JSON-LD structured data support nahi karti
(zyada tar modern ecommerce sites karti hain), to hum competitor ka page dekh
kar `product_selector`, `name_selector`, `price_selector` set karenge — ye
mujhe (Claude ko) competitor URL dete hi main check karke bata dunga.

### 4. GitHub Pages enable karein (dashboard live karne ke liye)
- Repository ke "Settings" tab mein jayein
- Left sidebar mein "Pages" par click karein
- "Branch" mein `main` select karein, folder `/docs` select karein
- "Save" karein
- Kuch minute baad aapko ek link milega jaise:
  `https://yourusername.github.io/price-compare/`
  Yehi aapka **live dashboard link** hai.

### 5. Workflow ko pehli dafa manually chalayein
- Repository ke "Actions" tab mein jayein
- "Price Comparison Update" workflow select karein
- "Run workflow" button par click karein
- 1-2 minute mein result ban jayega, aur dashboard link pe dikhega

Iske baad ye **har ghante khud chalega** — koi manual kaam nahi.

## Dashboard kya dikhata hai
- Har product: hamari price vs competitor price
- Farak (price difference) aur kaun sasta hai
- Jo products sirf hamare pass hain (competitor ke pass nahi)
- Jo products sirf competitor ke pass hain
- Search aur filter options

## Agar competitor site scrape na ho
Kuch websites bot-traffic block karti hain ya JavaScript se data load karti hain
(jo simple scraping se nahi milta). Aisi surat mein mujhe URL dein — main check
karke bataunga k alternative approach chahiye ya nahi.
