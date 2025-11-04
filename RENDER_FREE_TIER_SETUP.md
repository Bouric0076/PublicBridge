# PublicBridge - Render Free Tier Setup Guide

## 🎯 Overview

This guide explains how to deploy PublicBridge on Render's free tier, including handling media files without persistent storage.

## ✅ What's Configured for Free Tier

### 1. Updated `render.yaml`
- **Removed persistent disk** (paid feature)
- **Kept free PostgreSQL database**
- **Maintained web service configuration**

### 2. Media File Handling Solution
Since Render's free tier doesn't include persistent storage, we've implemented a **database-based file storage system**:

#### Features:
- ✅ Store small files (up to 5MB) directly in PostgreSQL database
- ✅ Automatic file size validation
- ✅ Base64 encoding support for images
- ✅ Migration tools for existing files

#### Usage:
```python
from utils.models import FreeTierFileStorage

# Save a file
db_file = FreeTierFileStorage.save_file(uploaded_file, max_size_mb=5)

# Retrieve a file
file_obj = FreeTierFileStorage.get_file(file_id)

# Delete a file
success = FreeTierFileStorage.delete_file(file_id)
```

## 🚀 Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Configure for Render free tier deployment"
git push origin main
```

### 2. Deploy on Render
1. Go to [https://render.com](https://render.com)
2. Sign up/in to your account
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Render will automatically detect your `render.yaml` file
6. Click "Apply" to deploy

### 3. Environment Variables
The following will be automatically configured:
- `DJANGO_SECRET_KEY` - Auto-generated
- `DEBUG=False` - Production mode
- `DATABASE_URL` - PostgreSQL connection
- `ALLOWED_HOSTS` - Your Render subdomain

## 📁 File Migration (If Needed)

If you have existing media files to migrate:

### Dry Run (Check what will be migrated):
```bash
python manage.py migrate_media_to_db --dry-run --max-size 5
```

### Actual Migration:
```bash
python manage.py migrate_media_to_db --max-size 5
```

## ⚠️ Free Tier Limitations

### Current Setup:
- ✅ **Web Service**: 1 free instance (sleeps after 15 min inactivity)
- ✅ **PostgreSQL**: 1GB storage, 100 max connections
- ✅ **Media Files**: Database storage (5MB max per file)
- ❌ **Persistent Storage**: Not available (removed from config)

### Recommendations:
1. **Keep files small** - Optimize images before upload
2. **Use external storage** - Consider AWS S3, Cloudinary, or similar for larger files
3. **Monitor database size** - PostgreSQL has 1GB limit
4. **Regular cleanup** - Delete unused files to save space

## 🔄 Future Upgrades

When you're ready to upgrade from free tier:

1. **Add persistent disk** back to `render.yaml`
2. **Switch to file-based storage** instead of database
3. **Consider external storage** like AWS S3 for scalability

## 🆘 Troubleshooting

### Common Issues:

1. **"Services require payment information"**
   - Ensure `disk:` section is removed from `render.yaml`
   - Check that database plan is set to `free`

2. **File upload fails**
   - Check file size (max 5MB for free tier)
   - Verify database has enough space

3. **Static files not loading**
   - Run `python manage.py collectstatic` locally first
   - Check that `whitenoise` is properly configured

## 📞 Support

For issues specific to:
- **Render deployment**: Check Render documentation
- **Django configuration**: Review Django deployment guides
- **Free tier limitations**: Consider upgrading or using external services

---

**Note**: This setup is optimized for Render's free tier. For production applications with high traffic or large file storage needs, consider upgrading to a paid plan or using dedicated file storage services.