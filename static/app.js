// MoogzTrade Web Demo - Frontend JavaScript
// Handles all interactions with the FastAPI backend

// Initialize Lucide icons
lucide.createIcons();

// Global state
let demoMode = true;
let priceChart = null;
let portfolioChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Load initial data
    loadModules();
    loadSystemHealth();
    loadPortfolioData();
    
    // Set up demo mode toggle
    setupDemoToggle();
    
    // Initialize charts
    initializeCharts();
    
    // Show security section by default
    showSection('security');
}

function setupDemoToggle() {
    const toggle = document.getElementById('demoToggle');
    toggle.addEventListener('click', function() {
        demoMode = !demoMode;
        const span = this.querySelector('span');
        if (demoMode) {
            this.classList.remove('bg-gray-600');
            this.classList.add('bg-green-600');
            span.classList.remove('translate-x-1');
            span.classList.add('translate-x-6');
        } else {
            this.classList.remove('bg-green-600');
            this.classList.add('bg-gray-600');
            span.classList.remove('translate-x-6');
            span.classList.add('translate-x-1');
        }
    });
}

function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Show selected section
    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.classList.remove('hidden');
        selectedSection.classList.add('fade-in');
    }
    
    // Update nav button states
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('bg-slate-700');
    });
    event.target.classList.add('bg-slate-700');
}

async function encryptData() {
    const plaintext = document.getElementById('plaintextInput').value;
    if (!plaintext) {
        showNotification('Please enter text to encrypt', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/encrypt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                plaintext: plaintext,
                demo_mode: demoMode
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('ciphertextOutput').textContent = data.ciphertext;
            document.getElementById('hmacOutput').textContent = data.hmac;
            showNotification('Data encrypted successfully', 'success');
        } else {
            showNotification(data.detail || 'Encryption failed', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

async function sendAgentCommand() {
    const prompt = document.getElementById('agentPrompt').value;
    if (!prompt) {
        showNotification('Please enter a command', 'error');
        return;
    }
    
    const terminal = document.getElementById('agentTerminal');
    
    // Add user command to terminal
    const userDiv = document.createElement('div');
    userDiv.className = 'text-blue-400';
    userDiv.textContent = `> ${prompt}`;
    terminal.appendChild(userDiv);
    
    // Add processing indicator
    const processingDiv = document.createElement('div');
    processingDiv.className = 'text-yellow-400';
    processingDiv.textContent = 'Processing...';
    terminal.appendChild(processingDiv);
    
    // Scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
    
    try {
        const response = await fetch('/api/agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                demo_mode: demoMode
            })
        });
        
        const data = await response.json();
        
        // Remove processing indicator
        terminal.removeChild(processingDiv);
        
        if (response.ok) {
            // Add agent responses
            data.response.forEach(responseLine => {
                const responseDiv = document.createElement('div');
                responseDiv.className = 'text-green-400';
                responseDiv.textContent = responseLine;
                terminal.appendChild(responseDiv);
            });
        } else {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-red-400';
            errorDiv.textContent = 'Error: ' + (data.detail || 'Processing failed');
            terminal.appendChild(errorDiv);
        }
    } catch (error) {
        terminal.removeChild(processingDiv);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-400';
        errorDiv.textContent = 'Network error: ' + error.message;
        terminal.appendChild(errorDiv);
    }
    
    // Clear input and scroll to bottom
    document.getElementById('agentPrompt').value = '';
    terminal.scrollTop = terminal.scrollHeight;
}

async function fetchMarketData() {
    const symbol = document.getElementById('symbolInput').value.toUpperCase();
    if (!symbol) {
        showNotification('Please enter a symbol', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/market-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: symbol,
                demo_mode: demoMode
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayMarketData(data);
            updatePriceChart(symbol, data.data);
            showNotification(`Market data loaded for ${symbol}`, 'success');
        } else {
            showNotification(data.detail || 'Failed to fetch market data', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

function displayMarketData(data) {
    const display = document.getElementById('marketDataDisplay');
    const marketData = data.data;
    
    const changeClass = marketData.change >= 0 ? 'text-green-400' : 'text-red-400';
    const changeSymbol = marketData.change >= 0 ? '+' : '';
    
    display.innerHTML = `
        <div class="space-y-2">
            <div class="flex justify-between">
                <span class="text-gray-400">Symbol:</span>
                <span class="font-bold">${data.symbol}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-400">Price:</span>
                <span class="font-bold text-xl">$${marketData.price.toFixed(2)}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-400">Change:</span>
                <span class="font-bold ${changeClass}">${changeSymbol}${marketData.change.toFixed(2)}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-400">Volume:</span>
                <span class="font-bold">${marketData.volume.toLocaleString()}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-400">Updated:</span>
                <span class="text-sm">${new Date(data.timestamp).toLocaleTimeString()}</span>
            </div>
        </div>
    `;
}

async function loadPortfolioData() {
    try {
        const response = await fetch('/api/portfolio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                demo_mode: demoMode
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayPortfolioData(data.portfolio);
            updatePortfolioChart(data.portfolio);
        }
    } catch (error) {
        console.error('Failed to load portfolio data:', error);
    }
}

function displayPortfolioData(portfolio) {
    document.getElementById('totalValue').textContent = `$${portfolio.total_value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('dailyReturn').textContent = `${portfolio.performance.daily_return >= 0 ? '+' : ''}${portfolio.performance.daily_return.toFixed(2)}%`;
    document.getElementById('sharpeRatio').textContent = portfolio.performance.sharpe_ratio.toFixed(2);
}

async function loadModules() {
    try {
        const response = await fetch('/api/modules');
        const data = await response.json();
        
        if (response.ok) {
            displayModules(data.modules);
        }
    } catch (error) {
        console.error('Failed to load modules:', error);
    }
}

function displayModules(modules) {
    const container = document.getElementById('modulesList');
    container.innerHTML = '';
    
    modules.forEach(module => {
        const moduleCard = document.createElement('div');
        moduleCard.className = 'bg-slate-800 border border-gray-600 rounded-lg p-4 hover-glow';
        moduleCard.innerHTML = `
            <div class="flex items-start justify-between mb-3">
                <div>
                    <h3 class="text-lg font-semibold text-white">${module.name}</h3>
                    <span class="text-xs px-2 py-1 rounded-full ${module.tier === 'Tier 1' ? 'bg-green-900 text-green-300' : 'bg-blue-900 text-blue-300'}">${module.tier}</span>
                    <span class="text-xs px-2 py-1 rounded-full bg-gray-700 text-gray-300 ml-2">${module.category}</span>
                </div>
                <i data-lucide="package" class="w-5 h-5 text-red-400"></i>
            </div>
            <p class="text-sm text-gray-400 mb-3">${module.description}</p>
            <div class="mb-3">
                <h4 class="text-xs font-semibold text-gray-300 mb-2">Features:</h4>
                <ul class="text-xs text-gray-400 space-y-1">
                    ${module.features.map(feature => `<li>• ${feature}</li>`).join('')}
                </ul>
            </div>
            <button onclick="runModuleDemo('${module.name}')" class="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-sm">
                Run Module Demo
            </button>
        `;
        container.appendChild(moduleCard);
    });
    
    // Reinitialize icons for new elements
    lucide.createIcons();
}

async function runModuleDemo(moduleName) {
    try {
        const response = await fetch('/api/module-demo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                module_name: moduleName,
                demo_mode: demoMode
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`${data.module.name} demo executed successfully`, 'success');
            console.log('Module demo data:', data.module);
        } else {
            showNotification(data.detail || 'Module demo failed', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

async function loadSystemHealth() {
    try {
        const response = await fetch('/api/system-health');
        const data = await response.json();
        
        if (response.ok) {
            displaySystemHealth(data.health);
        }
    } catch (error) {
        console.error('Failed to load system health:', error);
    }
}

function displaySystemHealth(health) {
    const container = document.getElementById('systemHealthDisplay');
    container.innerHTML = '';
    
    Object.entries(health).forEach(([component, status]) => {
        const statusClass = status.status === 'healthy' ? 'text-green-400' : 'text-red-400';
        const statusIcon = status.status === 'healthy' ? 'check-circle' : 'x-circle';
        
        const healthCard = document.createElement('div');
        healthCard.className = 'bg-slate-800 border border-gray-600 rounded-lg p-4';
        healthCard.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h3 class="text-lg font-semibold text-white capitalize">${component.replace('_', ' ')}</h3>
                <i data-lucide="${statusIcon}" class="w-5 h-5 ${statusClass}"></i>
            </div>
            <div class="space-y-1">
                <div class="flex justify-between">
                    <span class="text-sm text-gray-400">Status:</span>
                    <span class="text-sm font-semibold ${statusClass}">${status.status}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-sm text-gray-400">Last Check:</span>
                    <span class="text-xs">${new Date(status.last_check).toLocaleTimeString()}</span>
                </div>
            </div>
        `;
        container.appendChild(healthCard);
    });
    
    // Reinitialize icons for new elements
    lucide.createIcons();
}

function initializeCharts() {
    // Initialize price chart
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Price',
                data: [],
                borderColor: 'rgb(147, 51, 234)',
                backgroundColor: 'rgba(147, 51, 234, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'rgb(203, 213, 225)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'rgb(148, 163, 184)'
                    },
                    grid: {
                        color: 'rgba(71, 85, 105, 0.3)'
                    }
                },
                y: {
                    ticks: {
                        color: 'rgb(148, 163, 184)'
                    },
                    grid: {
                        color: 'rgba(71, 85, 105, 0.3)'
                    }
                }
            }
        }
    });
    
    // Initialize portfolio chart
    const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
    portfolioChart = new Chart(portfolioCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(168, 85, 247, 0.8)',
                    'rgba(251, 146, 60, 0.8)',
                    'rgba(236, 72, 153, 0.8)'
                ],
                borderColor: [
                    'rgb(34, 197, 94)',
                    'rgb(59, 130, 246)',
                    'rgb(168, 85, 247)',
                    'rgb(251, 146, 60)',
                    'rgb(236, 72, 153)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'rgb(203, 213, 225)'
                    }
                }
            }
        }
    });
}

function updatePriceChart(symbol, data) {
    // Generate mock historical data
    const labels = [];
    const prices = [];
    const basePrice = data.price;
    
    for (let i = 30; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString());
        
        // Generate random price variation
        const variation = (Math.random() - 0.5) * basePrice * 0.1;
        prices.push(basePrice + variation);
    }
    
    // Set current price as the last data point
    prices[prices.length - 1] = data.price;
    
    priceChart.data.labels = labels;
    priceChart.data.datasets[0].data = prices;
    priceChart.data.datasets[0].label = `${symbol} Price`;
    priceChart.update();
}

function updatePortfolioChart(portfolio) {
    const labels = portfolio.positions.map(pos => pos.symbol);
    const values = portfolio.positions.map(pos => pos.value);
    
    portfolioChart.data.labels = labels;
    portfolioChart.data.datasets[0].data = values;
    portfolioChart.update();
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg fade-in max-w-sm ${
        type === 'success' ? 'bg-green-600 text-white' :
        type === 'error' ? 'bg-red-600 text-white' :
        'bg-blue-600 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <i data-lucide="${
                type === 'success' ? 'check-circle' :
                type === 'error' ? 'x-circle' :
                'info'
            }" class="w-5 h-5"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    lucide.createIcons();
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatPercent(amount) {
    return `${amount >= 0 ? '+' : ''}${amount.toFixed(2)}%`;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to submit forms
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.id === 'plaintextInput') {
            encryptData();
        } else if (activeElement && activeElement.id === 'agentPrompt') {
            sendAgentCommand();
        } else if (activeElement && activeElement.id === 'symbolInput') {
            fetchMarketData();
        }
    }
    
    // Number keys to navigate sections
    if (event.key >= '1' && event.key <= '6') {
        const sections = ['security', 'agent', 'market', 'portfolio', 'modules', 'health'];
        const sectionIndex = parseInt(event.key) - 1;
        if (sectionIndex < sections.length) {
            showSection(sections[sectionIndex]);
        }
    }
});
