# PWA Icon Generation Instructions

To complete the PWA setup, you need to create high-resolution icons. Here are the required files and their specifications:

## Required Icon Files

Create these files in the `packages/web/public/` directory:

1. **icon-192.png** - 192x192 pixels
2. **icon-512.png** - 512x512 pixels
3. **icon-192-maskable.png** - 192x192 pixels (with safe zone for maskable icons)
4. **icon-512-maskable.png** - 512x512 pixels (with safe zone for maskable icons)

## Icon Design Guidelines

### Regular Icons (icon-192.png, icon-512.png)

- Use your app's main logo/icon
- Fill the entire canvas
- Use solid colors and clear shapes
- Ensure good contrast

### Maskable Icons (icon-192-maskable.png, icon-512-maskable.png)

- Design with a "safe zone" - keep important elements within the center 80% of the icon
- The outer 20% may be cropped or masked by the system
- Use a solid background color that works well when cropped
- Ensure the main logo/icon is clearly visible in the center

## Tools for Creating Icons

### Online Tools:

- [PWA Builder Icon Generator](https://www.pwabuilder.com/imageGenerator)
- [Favicon.io](https://favicon.io/favicon-generator/)
- [RealFaviconGenerator](https://realfavicongenerator.net/)

### Design Software:

- Figma (free)
- Adobe Illustrator
- GIMP (free)
- Canva

## Quick Setup with PWA Builder

1. Go to [PWA Builder](https://www.pwabuilder.com/imageGenerator)
2. Upload your high-resolution logo (at least 512x512)
3. Download the generated icon pack
4. Extract the files to `packages/web/public/`

## Testing Your PWA

After adding the icons:

1. Build your app: `npm run build`
2. Serve the built files locally
3. Open in Chrome/Edge
4. Look for the "Install" button in the address bar
5. Test the installation to see your new icons

## Icon Specifications Summary

| File                  | Size    | Purpose           | Safe Zone   |
| --------------------- | ------- | ----------------- | ----------- |
| icon-192.png          | 192x192 | Standard PWA icon | Full canvas |
| icon-512.png          | 512x512 | Standard PWA icon | Full canvas |
| icon-192-maskable.png | 192x192 | Maskable PWA icon | Center 80%  |
| icon-512-maskable.png | 512x512 | Maskable PWA icon | Center 80%  |

The manifest.json and HTML updates are already configured to use these icons.
