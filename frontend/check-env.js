#!/usr/bin/env node
/**
 * 前端环境变量检查脚本
 * 检查前端所需的环境变量是否正确配置
 */

const fs = require('fs');
const path = require('path');

function loadEnvFile(filename) {
  const envPath = path.join(__dirname, filename);
  if (!fs.existsSync(envPath)) {
    return null;
  }
  
  const content = fs.readFileSync(envPath, 'utf8');
  const env = {};
  
  content.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        env[key.trim()] = valueParts.join('=').trim();
      }
    }
  });
  
  return env;
}

function checkEnv() {
  console.log('🔍 前端环境变量检查');
  console.log('='.repeat(50));
  
  // 加载环境变量文件
  const envLocal = loadEnvFile('.env.local');
  const envExample = loadEnvFile('.env.example');
  
  if (!envLocal) {
    console.log('❌ 未找到 .env.local 文件');
    console.log('请复制 .env.example 为 .env.local');
    return false;
  }
  
  console.log('✅ 找到 .env.local 文件');
  
  // 检查API配置
  console.log('\n🌐 API配置检查');
  console.log('-'.repeat(30));
  
  const apiUrl = envLocal.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
  console.log(`API地址: ${apiUrl}`);
  
  if (apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1')) {
    console.log('✅ 开发环境配置');
  } else {
    console.log('🌐 生产环境配置');
  }
  
  // 检查功能开关
  console.log('\n🎛️  功能开关检查');
  console.log('-'.repeat(30));
  
  const features = {
    '文件上传': envLocal.NEXT_PUBLIC_ENABLE_FILE_UPLOAD !== 'false',
    '文本优化': envLocal.NEXT_PUBLIC_ENABLE_TEXT_OPTIMIZATION !== 'false',
    '会话管理': envLocal.NEXT_PUBLIC_ENABLE_SESSIONS !== 'false',
    '智能体详情': envLocal.NEXT_PUBLIC_SHOW_AGENT_DETAILS !== 'false'
  };
  
  Object.entries(features).forEach(([name, enabled]) => {
    console.log(`${name.padEnd(12)}: ${enabled ? '✅ 启用' : '❌ 禁用'}`);
  });
  
  // 检查文件配置
  console.log('\n📁 文件配置检查');
  console.log('-'.repeat(30));
  
  const maxFileSize = parseInt(envLocal.NEXT_PUBLIC_MAX_FILE_SIZE) || 52428800;
  const maxFileSizeMB = (maxFileSize / 1024 / 1024).toFixed(1);
  const supportedTypes = envLocal.NEXT_PUBLIC_SUPPORTED_FILE_TYPES || '.pdf,.docx,.txt,.md';
  
  console.log(`最大文件大小: ${maxFileSizeMB}MB`);
  console.log(`支持的类型: ${supportedTypes}`);
  
  // 检查调试配置
  console.log('\n🐛 调试配置检查');
  console.log('-'.repeat(30));
  
  const debug = envLocal.NEXT_PUBLIC_DEBUG === 'true';
  const showDevTools = envLocal.NEXT_PUBLIC_SHOW_DEV_TOOLS === 'true';
  
  console.log(`调试模式: ${debug ? '✅ 启用' : '❌ 禁用'}`);
  console.log(`开发工具: ${showDevTools ? '✅ 显示' : '❌ 隐藏'}`);
  
  if (debug && !apiUrl.includes('localhost')) {
    console.log('⚠️  警告: 生产环境启用了调试模式');
  }
  
  return true;
}

function checkDependencies() {
  console.log('\n📦 依赖检查');
  console.log('-'.repeat(30));
  
  try {
    const packageJson = require('./package.json');
    const dependencies = {
      ...packageJson.dependencies,
      ...packageJson.devDependencies
    };
    
    const requiredPackages = [
      'next',
      'react',
      'react-dom',
      'typescript',
      'tailwindcss'
    ];
    
    let allInstalled = true;
    
    requiredPackages.forEach(pkg => {
      if (dependencies[pkg]) {
        console.log(`${pkg.padEnd(20)}: ✅ ${dependencies[pkg]}`);
      } else {
        console.log(`${pkg.padEnd(20)}: ❌ 未安装`);
        allInstalled = false;
      }
    });
    
    if (!allInstalled) {
      console.log('\n❌ 缺少依赖包，请运行: npm install');
      return false;
    }
    
    // 检查node_modules
    if (fs.existsSync('./node_modules')) {
      console.log('\n✅ node_modules 目录存在');
    } else {
      console.log('\n❌ node_modules 目录不存在，请运行: npm install');
      return false;
    }
    
    return true;
  } catch (error) {
    console.log('❌ 读取 package.json 失败');
    return false;
  }
}

function checkBackendConnection() {
  console.log('\n🔌 后端连接检查');
  console.log('-'.repeat(30));
  
  const envLocal = loadEnvFile('.env.local');
  const apiUrl = envLocal?.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
  
  console.log(`正在检查后端连接: ${apiUrl}`);
  
  // 这里可以添加实际的网络检查，但为了保持简单，我们只做配置检查
  if (apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1')) {
    console.log('💡 提示: 请确保后端服务已启动');
    console.log('   启动命令: cd ../backend && python dev.py');
  }
  
  return true;
}

function main() {
  console.log('🚀 Solution Agent 前端环境检查');
  console.log('='.repeat(50));
  
  const envOk = checkEnv();
  const depsOk = checkDependencies();
  checkBackendConnection();
  
  console.log('\n' + '='.repeat(50));
  
  if (envOk && depsOk) {
    console.log('🎉 所有检查通过！可以启动前端服务器。');
    console.log('\n启动命令:');
    console.log('npm run dev        # 使用Turbopack (推荐)');
    console.log('npm run dev:legacy # 标准模式');
  } else {
    console.log('❌ 存在配置问题，请修复后重试。');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { checkEnv, checkDependencies };