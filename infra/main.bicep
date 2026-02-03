@description('The name of the environment (e.g., dev, staging, prod)')
param environment string = 'dev'

@description('The primary Azure region for resources')
param location string = resourceGroup().location

@description('The name prefix for all resources')
param namePrefix string = 'translate'

@description('Enable Azure OpenAI post-editor')
param enablePostEditor bool = false

@description('App Service SKU')
@allowed([
  'B1'
  'B2'
  'B3'
  'S1'
  'S2'
  'S3'
  'P1v2'
  'P2v2'
  'P3v2'
])
param appServiceSku string = 'B1'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Application: 'translation-service'
  ManagedBy: 'Bicep'
}

// Generate unique resource names
var uniqueSuffix = uniqueString(resourceGroup().id)
var translatorName = '${namePrefix}-translator-${environment}-${uniqueSuffix}'
var openaiName = '${namePrefix}-openai-${environment}-${uniqueSuffix}'
var appServicePlanName = '${namePrefix}-plan-${environment}-${uniqueSuffix}'
var appServiceName = '${namePrefix}-app-${environment}-${uniqueSuffix}'
var storageAccountName = '${namePrefix}${take(uniqueSuffix, 8)}'
var logAnalyticsName = '${namePrefix}-logs-${environment}-${uniqueSuffix}'
var appInsightsName = '${namePrefix}-insights-${environment}-${uniqueSuffix}'

// Azure Translator (Cognitive Services)
resource translator 'Microsoft.CognitiveServices/accounts@2025-10-01-preview' = {
  name: translatorName
  location: location
  kind: 'TextTranslation'
  sku: {
    name: 'S1'
  }
  properties: {
    customSubDomainName: translatorName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
  tags: tags
}

// Azure OpenAI (optional)
resource openai 'Microsoft.CognitiveServices/accounts@2025-10-01-preview' = if (enablePostEditor) {
  name: openaiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openaiName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
  tags: tags
}

// Storage Account (for glossary files and logs)
resource storageAccount 'Microsoft.Storage/storageAccounts@2025-06-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
  tags: tags
}

// Blob Services (for glossary storage)
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2025-06-01' = {
  parent: storageAccount
  name: 'default'
}

// Container for glossary files
resource glossaryContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-06-01' = {
  parent: blobService
  name: 'glossaries'
  properties: {
    publicAccess: 'None'
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2025-07-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
  tags: tags
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02-preview' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: 30
  }
  tags: tags
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2025-03-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: appServiceSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
  tags: tags
}

// App Service (Web App)
resource appService 'Microsoft.Web/sites@2025-03-01' = {
  name: appServiceName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'python run.py'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      appSettings: [
        {
          name: 'AZURE_TRANSLATOR_KEY'
          value: translator.listKeys().key1
        }
        {
          name: 'AZURE_TRANSLATOR_ENDPOINT'
          value: translator.properties.endpoint
        }
        {
          name: 'AZURE_TRANSLATOR_REGION'
          value: location
        }
        {
          name: 'AZURE_TRANSLATOR_CATEGORY'
          value: ''
        }
        {
          name: 'TARGET_LANGUAGE'
          value: 'nl'
        }
        {
          name: 'GLOSSARY_PATH'
          value: 'data/glossary.tsv,data/glossary-action.tsv'
        }
        {
          name: 'ENABLE_POST_EDITOR'
          value: enablePostEditor ? 'true' : 'false'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: enablePostEditor ? openai.properties.endpoint : ''
        }
        {
          name: 'AZURE_OPENAI_KEY'
          value: enablePostEditor ? openai.listKeys().key1 : ''
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT'
          value: 'gpt-4'
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2024-02-15-preview'
        }
        {
          name: 'HOST'
          value: '0.0.0.0'
        }
        {
          name: 'PORT'
          value: '8000'
        }
        {
          name: 'DEBUG'
          value: 'false'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
    }
  }
  tags: tags
}

// Outputs
output translatorEndpoint string = translator.properties.endpoint
output translatorName string = translator.name
output openaiEndpoint string = enablePostEditor ? openai.properties.endpoint : ''
output openaiName string = enablePostEditor ? openai.name : ''
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output appServiceName string = appService.name
output storageAccountName string = storageAccount.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
