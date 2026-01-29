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

/**
 * Analyze bubble using LPPL model
 */
let lpplFittedSeries = null;
let lpplForecastSeries = null;

async function analyzeBubble() {
    const bubbleLoading = document.getElementById('bubbleLoading');
    const bubbleResults = document.getElementById('bubbleResults');
    const analyzeButton = document.getElementById('analyzeBubble');

    // Show loading, hide results
    bubbleLoading.style.display = 'block';
    bubbleResults.style.display = 'none';
    analyzeButton.disabled = true;

    try {
        const response = await fetch(`/api/stock/${currentSymbol}/bubble/`);
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        displayBubbleResults(data);

    } catch (error) {
        const bubbleState = document.getElementById('bubbleState');
        const bubbleDetails = document.getElementById('bubbleDetails');
        bubbleState.className = 'alert alert-danger';
        bubbleState.innerHTML = `
            <strong><i class="bi bi-exclamation-triangle"></i> 분석 실패</strong>
            <p class="mb-0 mt-2">${error.message}</p>
        `;
        bubbleDetails.innerHTML = `
            <h6 class="border-bottom pb-2">문제 해결 방법</h6>
            <ul class="small">
                <li>최근 급등한 종목에서 더 잘 작동합니다</li>
                <li>최소 6개월~1년 이상의 데이터가 필요합니다</li>
                <li>횡보하는 종목보다는 추세가 뚜렷한 종목에 적합합니다</li>
                <li>다른 종목이나 시간대를 시도해보세요</li>
            </ul>
        `;
        bubbleResults.style.display = 'block';
    } finally {
        bubbleLoading.style.display = 'none';
        analyzeButton.disabled = false;
    }
}

function displayBubbleResults(data) {
    const bubbleState = document.getElementById('bubbleState');
    const bubbleDetails = document.getElementById('bubbleDetails');
    const bubbleResults = document.getElementById('bubbleResults');

    const confidence = data.confidence_indicator;
    const stats = confidence.statistics;

    // Set alert class based on state
    const stateColors = {
        'CRITICAL': 'alert-danger',
        'WARNING': 'alert-warning',
        'WATCH': 'alert-info',
        'NORMAL': 'alert-success'
    };

    bubbleState.className = `alert ${stateColors[confidence.state] || 'alert-secondary'}`;
    bubbleState.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <strong>${confidence.state}</strong>
                <p class="mb-0 small">${confidence.message}</p>
            </div>
            <div class="text-end">
                <div class="h3 mb-0">${confidence.confidence_indicator}%</div>
                <small>LPPLS Confidence</small>
            </div>
        </div>
    `;

    // Display detailed information
    bubbleDetails.innerHTML = `
        <h6 class="border-bottom pb-2">
            <i class="bi bi-graph-up"></i> Multi-Window Analysis
        </h6>
        <div class="small mb-3">
            <div class="mb-2">
                <strong>분석 방법:</strong> LPPLS Confidence Indicator<br>
                <span class="text-muted">
                    ${confidence.window_range.min}일~${confidence.window_range.max}일 구간을
                    ${confidence.window_range.step}일 단위로 분석
                </span>
            </div>
            <div class="mb-1">
                <strong>분석 기간:</strong> ${data.analysis_period.days}일
                (${data.analysis_period.start} ~ ${data.analysis_period.end})
            </div>
        </div>

        <h6 class="border-bottom pb-2">
            <i class="bi bi-bar-chart"></i> 통계
        </h6>
        <div class="small mb-3">
            <div class="row">
                <div class="col-6 mb-2">
                    <div class="text-muted small">총 윈도우</div>
                    <div class="h5 mb-0">${stats.total_windows}</div>
                </div>
                <div class="col-6 mb-2">
                    <div class="text-muted small">성공 피팅</div>
                    <div class="h5 mb-0 text-success">${stats.successful_fits}</div>
                </div>
                <div class="col-6 mb-2">
                    <div class="text-muted small">버블 조건 만족</div>
                    <div class="h5 mb-0 text-danger">${stats.bubble_windows}</div>
                </div>
                <div class="col-6 mb-2">
                    <div class="text-muted small">성공률</div>
                    <div class="h5 mb-0">${stats.success_rate}%</div>
                </div>
            </div>
        </div>

        <h6 class="border-bottom pb-2">
            <i class="bi bi-info-circle"></i> 해석
        </h6>
        <div class="small">
            <p class="mb-2">
                ${stats.successful_fits}개 윈도우 중 ${stats.bubble_windows}개(${confidence.confidence_indicator}%)가
                버블 조건을 만족했습니다.
            </p>
            ${confidence.confidence_indicator >= 60 ? `
                <div class="alert alert-danger alert-sm p-2 mb-2">
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong>위험:</strong> 대부분의 시간 윈도우에서 버블 신호가 감지되었습니다.
                    포지션 축소 및 리스크 관리를 고려하세요.
                </div>
            ` : confidence.confidence_indicator >= 40 ? `
                <div class="alert alert-warning alert-sm p-2 mb-2">
                    <i class="bi bi-exclamation-circle"></i>
                    <strong>경고:</strong> 상당수 윈도우에서 버블 패턴이 관찰됩니다.
                    주의 깊게 모니터링하세요.
                </div>
            ` : confidence.confidence_indicator >= 20 ? `
                <div class="alert alert-info alert-sm p-2 mb-2">
                    <i class="bi bi-info-circle"></i>
                    <strong>모니터링:</strong> 일부 윈도우에서만 버블 신호가 있습니다.
                    정기적으로 재분석하세요.
                </div>
            ` : `
                <div class="alert alert-success alert-sm p-2 mb-2">
                    <i class="bi bi-check-circle"></i>
                    <strong>정상:</strong> 대부분의 윈도우에서 정상 패턴을 보입니다.
                </div>
            `}
        </div>

        <details class="mt-3">
            <summary class="small text-muted" style="cursor: pointer;">
                <i class="bi bi-chevron-right"></i> 윈도우별 상세 결과 보기
            </summary>
            <div class="mt-2 small" style="max-height: 200px; overflow-y: auto;">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>윈도우</th>
                            <th>상태</th>
                            <th>버블</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${confidence.detailed_results.map(r => `
                            <tr>
                                <td>${r.window_size}일</td>
                                <td>
                                    ${r.success ?
                                        '<span class="badge bg-success">성공</span>' :
                                        '<span class="badge bg-danger">실패</span>'}
                                </td>
                                <td>
                                    ${r.is_bubble ?
                                        '<i class="bi bi-check-circle text-danger"></i>' :
                                        '<i class="bi bi-x-circle text-muted"></i>'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </details>
    `;

    // Add LPPL fitted line to chart
    if (data.fitted_prices && data.fitted_prices.length > 0) {
        // Remove existing LPPL lines
        if (lpplFittedSeries) {
            mainChart.removeSeries(lpplFittedSeries);
        }
        if (lpplForecastSeries) {
            mainChart.removeSeries(lpplForecastSeries);
        }

        // Add fitted line
        lpplFittedSeries = mainChart.addLineSeries({
            color: 'rgba(156, 39, 176, 0.8)',
            lineWidth: 2,
            title: 'LPPL Fit',
        });
        lpplFittedSeries.setData(data.fitted_prices);

        // Add forecast line if available
        if (data.forecast_prices && data.forecast_prices.length > 0) {
            lpplForecastSeries = mainChart.addLineSeries({
                color: 'rgba(156, 39, 176, 0.5)',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'LPPL Forecast',
            });
            lpplForecastSeries.setData(data.forecast_prices);
        }
    }

    bubbleResults.style.display = 'block';
}

// Add event listener when document loads
document.addEventListener('DOMContentLoaded', function() {
    const analyzeBubbleBtn = document.getElementById('analyzeBubble');
    if (analyzeBubbleBtn) {
        analyzeBubbleBtn.addEventListener('click', analyzeBubble);
    }
});
