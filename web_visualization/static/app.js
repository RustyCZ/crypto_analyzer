// Global variables
let comparisonData = null;
let uncorrelatedCoins = null;
let priceDistanceCoins = null;
let averageReturns = null;
let marketChart = null;
let comparisonChart = null;

// Fetch all data when page loads
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch all required data
        comparisonData = await fetchJSON('/api/comparison-data');
        uncorrelatedCoins = await fetchJSON('/api/uncorrelated-coins');
        priceDistanceCoins = await fetchJSON('/api/price-distance-coins');
        averageReturns = await fetchJSON('/api/average-returns');
        
        // Update summary numbers
        updateSummaryNumbers();
        
        // Populate coin selector
        populateCoinSelector();
        
        // Initialize charts
        initializeMarketChart();
        initializeComparisonChart();
        
        // Populate tables
        populateUncorrelatedTable();
        populatePriceDistanceTable();
        populateAllCoinsTable();
        
        // Set up tab switching
        setupTabs();
        
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Failed to load data. Please check the console for details.');
    }
});

// Fetch JSON data from API
async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Update summary numbers
function updateSummaryNumbers() {
    document.getElementById('totalCoins').textContent = Object.keys(averageReturns).length;
    document.getElementById('uncorrelatedCoins').textContent = uncorrelatedCoins.length;
    document.getElementById('priceDistanceCoins').textContent = priceDistanceCoins.length;
}

// Populate coin selector dropdown
function populateCoinSelector() {
    const select = document.getElementById('coinSelect');
    
    // Add all price distance outlier coins
    priceDistanceCoins.forEach(coin => {
        const option = document.createElement('option');
        option.value = coin.symbol;
        option.textContent = coin.symbol;
        select.appendChild(option);
    });
    
    // Add event listener for coin selection
    select.addEventListener('change', updateComparisonChart);
}

// Initialize market average chart
function initializeMarketChart() {
    const ctx = document.getElementById('marketChart').getContext('2d');
    
    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: comparisonData.dates,
            datasets: [{
                label: 'Market Average',
                data: comparisonData.market_avg,
                borderColor: '#16213e',
                backgroundColor: 'rgba(22, 33, 62, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Market Average Cumulative Return',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Cumulative Return'
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Initialize comparison chart
function initializeComparisonChart() {
    const ctx = document.getElementById('comparisonChart').getContext('2d');
    
    comparisonChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: comparisonData.dates,
            datasets: [{
                label: 'Market Average',
                data: comparisonData.market_avg,
                borderColor: '#16213e',
                backgroundColor: 'rgba(22, 33, 62, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Coin vs Market Comparison',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Cumulative Return'
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Update comparison chart when coin is selected
function updateComparisonChart() {
    const select = document.getElementById('coinSelect');
    const selectedCoin = select.value;
    
    if (!selectedCoin) {
        // If no coin selected, show only market average
        comparisonChart.data.datasets = [{
            label: 'Market Average',
            data: comparisonData.market_avg,
            borderColor: '#16213e',
            backgroundColor: 'rgba(22, 33, 62, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.1
        }];
    } else {
        // If coin selected, show both market average and selected coin
        const coinData = comparisonData.coins[selectedCoin];
        
        comparisonChart.data.datasets = [
            {
                label: 'Market Average',
                data: comparisonData.market_avg,
                borderColor: '#16213e',
                backgroundColor: 'rgba(22, 33, 62, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            },
            {
                label: selectedCoin,
                data: coinData.data,
                borderColor: '#e94560',
                backgroundColor: 'rgba(233, 69, 96, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            }
        ];
        
        comparisonChart.options.plugins.title.text = `${selectedCoin} vs Market Comparison`;
    }
    
    comparisonChart.update();
}

// Populate uncorrelated coins table
function populateUncorrelatedTable() {
    const tbody = document.querySelector('#uncorrelatedTable tbody');
    tbody.innerHTML = '';
    
    uncorrelatedCoins.forEach(coin => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td>${coin.symbol}</td>
            <td>${coin.avg_correlation.toFixed(4)}</td>
            <td>${(averageReturns[coin.symbol]?.cumulative_return * 100).toFixed(2)}%</td>
        `;
        
        tbody.appendChild(tr);
    });
}

// Populate price distance coins table
function populatePriceDistanceTable() {
    const tbody = document.querySelector('#priceDistanceTable tbody');
    tbody.innerHTML = '';
    
    priceDistanceCoins.forEach(coin => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td>${coin.symbol}</td>
            <td>${(coin.price_distance * 100).toFixed(2)}%</td>
            <td>${(coin.cumulative_return * 100).toFixed(2)}%</td>
            <td>${(coin.market_return * 100).toFixed(2)}%</td>
        `;
        
        tbody.appendChild(tr);
    });
}

// Populate all coins table
function populateAllCoinsTable() {
    const tbody = document.querySelector('#allCoinsTable tbody');
    tbody.innerHTML = '';
    
    Object.entries(averageReturns).forEach(([symbol, data]) => {
        const tr = document.createElement('tr');
        
        // Find correlation data for this coin
        const correlationData = uncorrelatedCoins.find(c => c.symbol === symbol);
        const correlation = correlationData ? correlationData.avg_correlation : '-';
        
        // Find price distance data for this coin
        const distanceData = priceDistanceCoins.find(c => c.symbol === symbol);
        const priceDistance = distanceData ? distanceData.price_distance : '-';
        
        tr.innerHTML = `
            <td>${symbol}</td>
            <td>${(data.avg_daily_return * 100).toFixed(4)}%</td>
            <td>${(data.cumulative_return * 100).toFixed(2)}%</td>
            <td>${typeof correlation === 'number' ? correlation.toFixed(4) : correlation}</td>
            <td>${typeof priceDistance === 'number' ? (priceDistance * 100).toFixed(2) + '%' : priceDistance}</td>
        `;
        
        tbody.appendChild(tr);
    });
}

// Set up tab switching
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}
