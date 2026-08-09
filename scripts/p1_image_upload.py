from pathlib import Path
import re
hp=Path('index.html'); bp=Path('functions/index.js'); h=hp.read_text(); b=bp.read_text()

def replace_fn(src,name,new):
    m=re.search(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',src,re.M)
    if not m: raise SystemExit('fn '+name)
    start=m.start(); brace=src.find('{',m.start()); i=brace+1; d=1; st='code'; esc=False
    while i<len(src) and d:
        c=src[i]; n=src[i+1] if i+1<len(src) else ''
        if st=='line':
            if c=='\n': st='code'
        elif st=='block':
            if c=='*' and n=='/': st='code'; i+=1
        elif st in ('sq','dq','tpl'):
            if esc: esc=False
            elif c=='\\': esc=True
            elif st=='sq' and c=="'": st='code'
            elif st=='dq' and c=='"': st='code'
            elif st=='tpl' and c=='`': st='code'
        else:
            if c=='/' and n=='/': st='line'; i+=1
            elif c=='/' and n=='*': st='block'; i+=1
            elif c=="'": st='sq'
            elif c=='"': st='dq'
            elif c=='`': st='tpl'
            elif c=='{': d+=1
            elif c=='}': d-=1
        i+=1
    return src[:start]+new+src[i:]

# Backend: Admin SDK Storage, no new package dependency.
if "firebase-admin/storage" not in b:
    b=b.replace("const { getDatabase } = require('firebase-admin/database');","const { getDatabase } = require('firebase-admin/database');\nconst { getStorage } = require('firebase-admin/storage');\nconst { randomUUID } = require('crypto');",1)

marker='''exports.updateOrder = onCall(async (request) => {\n'''
if 'exports.uploadProductImage' not in b:
    code='''exports.uploadProductImage = onCall(async (request) => {\n  await getEmployeeForRequest(request, 1);\n  const contentType = cleanText(request.data?.contentType, 80).toLowerCase();\n  if (!['image/jpeg', 'image/png', 'image/webp'].includes(contentType)) throw new HttpsError('invalid-argument', 'Only JPG, PNG, or WEBP images are allowed.');\n  const encoded = cleanText(request.data?.base64, 8 * 1024 * 1024);\n  if (!encoded || !/^[A-Za-z0-9+/=]+$/.test(encoded)) throw new HttpsError('invalid-argument', 'Invalid image data.');\n  const buffer = Buffer.from(encoded, 'base64');\n  if (!buffer.length || buffer.length > 5 * 1024 * 1024) throw new HttpsError('invalid-argument', 'Image must be 5 MB or smaller.');\n  const ext = contentType === 'image/png' ? 'png' : contentType === 'image/webp' ? 'webp' : 'jpg';\n  const bucketName = process.env.FIREBASE_STORAGE_BUCKET || `${process.env.GCLOUD_PROJECT}.firebasestorage.app`;\n  const bucket = getStorage().bucket(bucketName);\n  const token = randomUUID();\n  const path = `products/${Date.now()}-${randomUUID()}.${ext}`;\n  await bucket.file(path).save(buffer, { resumable: false, metadata: { contentType, cacheControl: 'public,max-age=31536000,immutable', metadata: { firebaseStorageDownloadTokens: token } } });\n  const url = `https://firebasestorage.googleapis.com/v0/b/${encodeURIComponent(bucket.name)}/o/${encodeURIComponent(path)}?alt=media&token=${token}`;\n  return { url };\n});\n\n'''
    if marker not in b: raise SystemExit('backend marker')
    b=b.replace(marker,code+marker,1)

new_upload='''        async function handleImageUpload(event) {\n            const file=event.target.files?.[0]; if(!file)return;\n            const allowed=['image/jpeg','image/png','image/webp'];\n            if(!allowed.includes(file.type)){alert('Please select a JPG, PNG, or WEBP image.');event.target.value='';return;}\n            if(file.size>5*1024*1024){alert('Image must be 5MB or smaller.');event.target.value='';return;}\n            const placeholder=document.getElementById('uploadPlaceholder'); const preview=document.getElementById('imagePreview'); const change=document.getElementById('changeImageBtn');\n            const original=placeholder.innerHTML; placeholder.innerHTML='<div class="upload-icon">⏳</div><div class="upload-text">Uploading image…</div>';\n            try {\n                const base64=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onerror=()=>reject(reader.error);reader.onload=()=>resolve(String(reader.result).split(',')[1]||'');reader.readAsDataURL(file);});\n                const upload=cloudFunctions.httpsCallable('uploadProductImage'); const response=await upload({base64,contentType:file.type}); const url=response.data?.url; if(!url)throw new Error('Upload completed without a file URL.');\n                document.getElementById('productImageData').value=url; preview.src=url; preview.classList.add('active'); placeholder.style.display='none'; change.style.display='block'; document.getElementById('imageUploadArea').classList.add('has-image');\n            } catch(error) { console.error('Product image upload failed:',error); placeholder.innerHTML=original; placeholder.style.display='block'; alert(error?.message||'Unable to upload image.'); event.target.value=''; }\n        }\n'''
h=replace_fn(h,'handleImageUpload',new_upload)

# Main upload input label now reflects server storage rather than DB base64.
h=h.replace('JPG, PNG, or WEBP (Max 5MB)','JPG, PNG, or WEBP (Max 5MB · securely uploaded)',1)

hp.write_text(h); bp.write_text(b); print('secure image upload batch applied')
