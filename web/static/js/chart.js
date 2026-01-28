/**
 * Korean Stock Quant - Chart Module
 * Uses Lightweight Charts (TradingView) for stock visualization
 */

// Global chart references
let mainChart = null;
let volumeChart = null;
let rsiChart = null;
let stochChart = null;
let candlestickSeries = null;
let volumeSeries = null;
let bbUpperSeries = null;
let bbMiddleSeries = null;
let bbLowerSeries = null;
let rsiSeries = null;
let stochKSeries = null;
let stochDSeries = null;
let currentSymbol = null;

// Signal markers
let signalMarkers = [];

/**
 * Initialize the chart with stock data
 */
async function initChart(symbol) {
    currentSymbol = symbol;

    // Create main chart (light mode)
    const chartContainer = document.getElementById('chart-container');
    mainChart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 500,
        layout: {
            background: { type: 'solid', color: '#ffffff' },
            textColor: '#333333',
        },
        grid: {
            vertLines: { color: '#e0e0e0' },
            horzLines: { color: '#e0e0e0' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#cccccc',
        },
        timeScale: {
            borderColor: '#cccccc',
            timeVisible: true,
        },
    });

    // Add candlestick series with larger size
    candlestickSeries = mainChart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderDownColor: '#ef5350',
        borderUpColor: '#26a69a',
        wickDownColor: '#ef5350',
        wickUpColor: '#26a69a',
    });

    // Apply larger candlestick width
    mainChart.applyOptions({
        timeScale: {
            barSpacing: 12,
            minBarSpacing: 6,
        },
    });

    // Create separate volume chart (light mode)
    const volumeContainer = document.getElementById('volume-chart-container');
    volumeChart = LightweightCharts.createChart(volumeContainer, {
        width: volumeContainer.clientWidth,
        height: 150,
        layout: {
            background: { type: 'solid', color: '#ffffff' },
            textColor: '#333333',
        },
        grid: {
            vertLines: { color: '#e0e0e0' },
            horzLines: { color: '#e0e0e0' },
        },
        rightPriceScale: {
            borderColor: '#cccccc',
        },
        timeScale: {
            borderColor: '#cccccc',
            visible: false,
        },
    });

    // Add volume series to volume chart
    volumeSeries = volumeChart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: {
            type: 'volume',
        },
        priceScaleId: 'right',
    });

    // Load initial data
    await loadOHLCVData();

    // Setup event listeners
    setupEventListeners();

    // Hide loading indicator
    document.getElementById('loading-indicator').style.display = 'none';

    // Handle resize
    window.addEventListener('resize', () => {
        mainChart.applyOptions({ width: chartContainer.clientWidth });
        if (volumeChart) {
            volumeChart.applyOptions({ width: document.getElementById('volume-chart-container').clientWidth });
        }
        if (rsiChart) {
            rsiChart.applyOptions({ width: document.getElementById('rsi-chart-container').clientWidth });
        }
        if (stochChart) {
            stochChart.applyOptions({ width: document.getElementById('stoch-chart-container').clientWidth });
        }
    });
}

/**
 * Load OHLCV data from API
 */
async function loadOHLCVData() {
    const timeRange = document.getElementById('timeRange').value;
    const { start, end } = getDateRange(timeRange);

    document.getElementById('loading-indicator').style.display = 'block';

    try {
        const response = await fetch(`/api/stock/${currentSymbol}/ohlcv/?start=${start}&end=${end}`);
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Format data for candlestick
        const candleData = data.data.map(d => ({
            time: d.time,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));

        // Format data for volume
        const volumeData = data.data.map(d => ({
            time: d.time,
            value: d.volume,
            color: d.close >= d.open ? '#26a69a80' : '#ef535080',
        }));

        candlestickSeries.setData(candleData);
        volumeSeries.setData(volumeData);

        // Fit content
        mainChart.timeScale().fitContent();
        volumeChart.timeScale().fitContent();

        // Sync volume chart time scale with main chart
        mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (volumeChart && range) {
                volumeChart.timeScale().setVisibleLogicalRange(range);
            }
        });

    } catch (error) {
        console.error('Failed to load OHLCV data:', error);
        alert('데이터를 불러오는데 실패했습니다: ' + error.message);
    } finally {
        document.getElementById('loading-indicator').style.display = 'none';
    }
}

/**
 * Calculate date range based on selection
 */
function getDateRange(range) {
    const end = new Date();
    let start = new Date();

    switch (range) {
        case '3m':
            start.setMonth(start.getMonth() - 3);
            break;
        case '6m':
            start.setMonth(start.getMonth() - 6);
            break;
        case '1y':
            start.setFullYear(start.getFullYear() - 1);
            break;
        case '2y':
            start.setFullYear(start.getFullYear() - 2);
            break;
        case '5y':
            start.setFullYear(start.getFullYear() - 5);
            break;
        case '10y':
            start.setFullYear(start.getFullYear() - 10);
            break;
        default:
            start.setFullYear(start.getFullYear() - 1);
    }

    return {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0],
    };
}

/**
 * Setup event listeners for controls
 */
function setupEventListeners() {
    // RSI toggle
    document.getElementById('toggleRSI').addEventListener('change', function() {
        document.getElementById('rsi-params').style.display = this.checked ? 'block' : 'none';
        if (this.checked) {
            loadRSIIndicator();
        } else {
            hideRSIChart();
        }
    });

    // Bollinger Bands toggle
    document.getElementById('toggleBB').addEventListener('change', function() {
        document.getElementById('bb-params').style.display = this.checked ? 'block' : 'none';
        if (this.checked) {
            loadBBIndicator();
        } else {
            hideBBOverlay();
        }
    });

    // Stochastic toggle
    document.getElementById('toggleStoch').addEventListener('change', function() {
        document.getElementById('stoch-params').style.display = this.checked ? 'block' : 'none';
        if (this.checked) {
            loadStochIndicator();
        } else {
            hideStochChart();
        }
    });

    // Signals toggle
    document.getElementById('toggleSignals').addEventListener('change', function() {
        document.getElementById('signal-indicator-select').style.display = this.checked ? 'block' : 'none';
        document.getElementById('signals-list').style.display = this.checked ? 'block' : 'none';
        if (this.checked) {
            loadSignals();
        } else {
            clearSignalMarkers();
        }
    });

    // Signal indicator change
    document.getElementById('signalIndicator').addEventListener('change', function() {
        if (document.getElementById('toggleSignals').checked) {
            loadSignals();
        }
    });

    // Time range change
    document.getElementById('timeRange').addEventListener('change', async function() {
        await loadOHLCVData();

        // Reload active indicators
        if (document.getElementById('toggleRSI').checked) loadRSIIndicator();
        if (document.getElementById('toggleBB').checked) loadBBIndicator();
        if (document.getElementById('toggleStoch').checked) loadStochIndicator();
        if (document.getElementById('toggleSignals').checked) loadSignals();
    });

    // Parameter changes
    ['rsiPeriod', 'rsiOverbought', 'rsiOversold'].forEach(id => {
        document.getElementById(id).addEventListener('change', function() {
            if (document.getElementById('toggleRSI').checked) loadRSIIndicator();
        });
    });

    ['bbPeriod', 'bbStdDev'].forEach(id => {
        document.getElementById(id).addEventListener('change', function() {
            if (document.getElementById('toggleBB').checked) loadBBIndicator();
        });
    });

    ['stochK', 'stochD'].forEach(id => {
        document.getElementById(id).addEventListener('change', function() {
            if (document.getElementById('toggleStoch').checked) loadStochIndicator();
        });
    });
}

/**
 * Load RSI indicator
 */
async function loadRSIIndicator() {
    const timeRange = document.getElementById('timeRange').value;
    const { start, end } = getDateRange(timeRange);

    const period = document.getElementById('rsiPeriod').value;
    const overbought = document.getElementById('rsiOverbought').value;
    const oversold = document.getElementById('rsiOversold').value;

    try {
        const response = await fetch(
            `/api/stock/${currentSymbol}/indicator/RSI/?start=${start}&end=${end}&period=${period}&overbought=${overbought}&oversold=${oversold}`
        );
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Create RSI chart if not exists
        if (!rsiChart) {
            const container = document.getElementById('rsi-chart-container');
            container.style.display = 'block';

            rsiChart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 150,
                layout: {
                    background: { type: 'solid', color: '#ffffff' },
                    textColor: '#333333',
                },
                grid: {
                    vertLines: { color: '#e0e0e0' },
                    horzLines: { color: '#e0e0e0' },
                },
                rightPriceScale: {
                    borderColor: '#cccccc',
                },
                timeScale: {
                    borderColor: '#cccccc',
                    visible: false,
                },
            });

            rsiSeries = rsiChart.addLineSeries({
                color: '#f48fb1',
                lineWidth: 2,
            });
        }

        // Set RSI data
        rsiSeries.setData(data.data.rsi);

        // Sync time scale with main chart
        mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (rsiChart) {
                rsiChart.timeScale().setVisibleLogicalRange(range);
            }
        });

    } catch (error) {
        console.error('Failed to load RSI:', error);
    }
}

/**
 * Hide RSI chart
 */
function hideRSIChart() {
    if (rsiChart) {
        rsiChart.remove();
        rsiChart = null;
        rsiSeries = null;
    }
    document.getElementById('rsi-chart-container').style.display = 'none';
}

/**
 * Load Bollinger Bands indicator
 */
async function loadBBIndicator() {
    const timeRange = document.getElementById('timeRange').value;
    const { start, end } = getDateRange(timeRange);

    const period = document.getElementById('bbPeriod').value;
    const stdDev = document.getElementById('bbStdDev').value;

    try {
        const response = await fetch(
            `/api/stock/${currentSymbol}/indicator/BB/?start=${start}&end=${end}&period=${period}&std_dev=${stdDev}`
        );
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Remove existing BB series
        hideBBOverlay();

        // Add BB series to main chart
        bbUpperSeries = mainChart.addLineSeries({
            color: 'rgba(33, 150, 243, 0.5)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
        });

        bbMiddleSeries = mainChart.addLineSeries({
            color: 'rgba(33, 150, 243, 0.8)',
            lineWidth: 1,
        });

        bbLowerSeries = mainChart.addLineSeries({
            color: 'rgba(33, 150, 243, 0.5)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
        });

        bbUpperSeries.setData(data.data.bb_upper);
        bbMiddleSeries.setData(data.data.bb_middle);
        bbLowerSeries.setData(data.data.bb_lower);

    } catch (error) {
        console.error('Failed to load Bollinger Bands:', error);
    }
}

/**
 * Hide Bollinger Bands overlay
 */
function hideBBOverlay() {
    if (bbUpperSeries) {
        mainChart.removeSeries(bbUpperSeries);
        bbUpperSeries = null;
    }
    if (bbMiddleSeries) {
        mainChart.removeSeries(bbMiddleSeries);
        bbMiddleSeries = null;
    }
    if (bbLowerSeries) {
        mainChart.removeSeries(bbLowerSeries);
        bbLowerSeries = null;
    }
}

/**
 * Load Stochastic indicator
 */
async function loadStochIndicator() {
    const timeRange = document.getElementById('timeRange').value;
    const { start, end } = getDateRange(timeRange);

    const kPeriod = document.getElementById('stochK').value;
    const dPeriod = document.getElementById('stochD').value;

    try {
        const response = await fetch(
            `/api/stock/${currentSymbol}/indicator/STOCH/?start=${start}&end=${end}&k_period=${kPeriod}&d_period=${dPeriod}`
        );
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Create Stochastic chart if not exists
        if (!stochChart) {
            const container = document.getElementById('stoch-chart-container');
            container.style.display = 'block';

            stochChart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 150,
                layout: {
                    background: { type: 'solid', color: '#ffffff' },
                    textColor: '#333333',
                },
                grid: {
                    vertLines: { color: '#e0e0e0' },
                    horzLines: { color: '#e0e0e0' },
                },
                rightPriceScale: {
                    borderColor: '#cccccc',
                },
                timeScale: {
                    borderColor: '#cccccc',
                    visible: false,
                },
            });

            stochKSeries = stochChart.addLineSeries({
                color: '#4caf50',
                lineWidth: 2,
            });

            stochDSeries = stochChart.addLineSeries({
                color: '#ff9800',
                lineWidth: 2,
            });
        }

        // Set Stochastic data
        stochKSeries.setData(data.data.stoch_k);
        stochDSeries.setData(data.data.stoch_d);

        // Sync time scale with main chart
        mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (stochChart) {
                stochChart.timeScale().setVisibleLogicalRange(range);
            }
        });

    } catch (error) {
        console.error('Failed to load Stochastic:', error);
    }
}

/**
 * Hide Stochastic chart
 */
function hideStochChart() {
    if (stochChart) {
        stochChart.remove();
        stochChart = null;
        stochKSeries = null;
        stochDSeries = null;
    }
    document.getElementById('stoch-chart-container').style.display = 'none';
}

/**
 * Load trading signals
 */
async function loadSignals() {
    const timeRange = document.getElementById('timeRange').value;
    const { start, end } = getDateRange(timeRange);
    const indicator = document.getElementById('signalIndicator').value;

    try {
        const response = await fetch(
            `/api/stock/${currentSymbol}/signals/${indicator}/?start=${start}&end=${end}`
        );
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Clear existing markers
        clearSignalMarkers();

        // Add markers to candlestick series
        signalMarkers = data.signals.map(s => ({
            time: s.time,
            position: s.signal === 1 ? 'belowBar' : 'aboveBar',
            color: s.signal === 1 ? '#26a69a' : '#ef5350',
            shape: s.signal === 1 ? 'arrowUp' : 'arrowDown',
            text: s.signal === 1 ? 'BUY' : 'SELL',
        }));

        candlestickSeries.setMarkers(signalMarkers);

        // Display signals list
        const signalsContent = document.getElementById('signals-content');
        if (data.signals.length === 0) {
            signalsContent.innerHTML = '<p class="text-muted small">최근 신호가 없습니다.</p>';
        } else {
            signalsContent.innerHTML = data.signals.slice(-10).reverse().map(s => `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="small">${s.time}</span>
                    <span class="badge ${s.signal === 1 ? 'bg-success' : 'bg-danger'}">
                        ${s.signal === 1 ? '매수' : '매도'}
                    </span>
                    <span class="small">${s.price.toLocaleString()}</span>
                </div>
            `).join('');
        }

    } catch (error) {
        console.error('Failed to load signals:', error);
    }
}

/**
 * Clear signal markers from chart
 */
function clearSignalMarkers() {
    signalMarkers = [];
    if (candlestickSeries) {
        candlestickSeries.setMarkers([]);
    }
    const signalsContent = document.getElementById('signals-content');
    if (signalsContent) {
        signalsContent.innerHTML = '';
    }
}
