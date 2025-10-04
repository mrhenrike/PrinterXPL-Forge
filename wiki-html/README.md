# PrinterReaper HTML Wiki

Standalone HTML documentation for embedding in websites.

## Files

- `index.html` - Main homepage
- `commands.html` - Commands reference  
- `style.css` - Shared stylesheet (optional)

## Usage

### Local Testing

```bash
# Start HTTP server
python -m http.server 8000 --directory wiki-html

# Open browser
http://localhost:8000
```

### Deploy to Website

Upload all HTML files to your web server:

```bash
scp wiki-html/*.html user@server:/var/www/html/printerreaper/
```

### GitHub Pages

Can also be deployed to GitHub Pages for free hosting.

## Features

- ✅ Responsive design
- ✅ Professional styling
- ✅ No external dependencies
- ✅ Fast loading
- ✅ Mobile-friendly

## Customization

Edit the HTML files to match your website's theme.

---

**Version**: 2.4.2  
**Last Updated**: October 4, 2025

