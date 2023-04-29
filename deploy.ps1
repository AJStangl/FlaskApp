#az login
Compress-Archive -Path D:\code\repos\CurationFlask\* -DestinationPath CurationFlask.zip -Update
az webapp deploy --name curation-app --resource-group aj-personal-rg --src-path CurationFlask.zip