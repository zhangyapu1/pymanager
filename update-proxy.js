// Cloudflare Workers 更新代理服务
// 部署地址示例：https://update-proxy.pymanager.workers.dev

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

// 配置
const CONFIG = {
  // GitHub 仓库配置
  repoOwner: 'zhangyapu1',
  repoName: 'pymanager',
  // 允许的来源（安全限制）
  allowedOrigins: ['*'],
  // 缓存时间（秒）
  cacheTTL: 60 * 5 // 5分钟
}

async function handleRequest(request) {
  const url = new URL(request.url)
  const path = url.pathname
  
  // CORS 处理
  if (request.method === 'OPTIONS') {
    return handleOptions(request)
  }
  
  // 版本检查端点
  if (path === '/api/version') {
    return handleVersionCheck()
  }
  
  // 下载代理端点
  if (path === '/api/download') {
    return handleDownloadProxy(request)
  }
  
  return new Response('Not Found', { status: 404 })
}

function handleOptions(request) {
  const origin = request.headers.get('Origin')
  const headers = {
    'Access-Control-Allow-Origin': origin || '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  }
  return new Response(null, { headers })
}

async function handleVersionCheck() {
  try {
    // 从 GitHub API 获取最新版本
    const githubUrl = `https://api.github.com/repos/${CONFIG.repoOwner}/${CONFIG.repoName}/releases/latest`
    const response = await fetch(githubUrl, {
      headers: { 'Accept': 'application/json' }
    })
    
    if (!response.ok) {
      return new Response('Failed to fetch version', { status: response.status })
    }
    
    const data = await response.json()
    const latestVersion = data.tag_name?.replace('v', '') || ''
    const downloadUrl = `/api/download?tag=${encodeURIComponent(data.tag_name || '')}`
    
    const result = {
      version: latestVersion,
      downloadUrl: downloadUrl,
      source: 'Cloudflare Workers'
    }
    
    return new Response(JSON.stringify(result), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': `max-age=${CONFIG.cacheTTL}`
      }
    })
  } catch (error) {
    return new Response(`Error: ${error.message}`, { status: 500 })
  }
}

async function handleDownloadProxy(request) {
  try {
    const url = new URL(request.url)
    const tag = url.searchParams.get('tag') || 'latest'
    
    // 构建 GitHub 下载链接
    let githubDownloadUrl
    
    if (tag === 'latest') {
      // 获取最新 release 的下载链接
      const releasesUrl = `https://api.github.com/repos/${CONFIG.repoOwner}/${CONFIG.repoName}/releases/latest`
      const releasesResponse = await fetch(releasesUrl, {
        headers: { 'Accept': 'application/json' }
      })
      
      if (!releasesResponse.ok) {
        return new Response('Failed to fetch releases', { status: releasesResponse.status })
      }
      
      const releaseData = await releasesResponse.json()
      const assets = releaseData.assets || []
      
      // 优先选择 .zip 或 .exe 文件
      const asset = assets.find(a => 
        a.name.endsWith('.zip') || a.name.endsWith('.exe')
      ) || assets[0]
      
      if (asset) {
        githubDownloadUrl = asset.browser_download_url
      } else {
        // Fallback to source code
        githubDownloadUrl = releaseData.zipball_url
      }
    } else {
      // 使用指定 tag 的源码包
      githubDownloadUrl = `https://github.com/${CONFIG.repoOwner}/${CONFIG.repoName}/archive/refs/tags/${tag}.zip`
    }
    
    // 代理请求到 GitHub
    const response = await fetch(githubDownloadUrl)
    
    if (!response.ok) {
      return new Response('Failed to download from GitHub', { status: response.status })
    }
    
    // 返回响应（流式传输）
    return new Response(response.body, {
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/octet-stream',
        'Content-Length': response.headers.get('Content-Length'),
        'Content-Disposition': response.headers.get('Content-Disposition') || `attachment; filename="pymanager-${tag}.zip"`,
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-cache'
      }
    })
  } catch (error) {
    return new Response(`Download failed: ${error.message}`, { status: 500 })
  }
}
