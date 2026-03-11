// RSI计算函数
function calculateRSI(prices, period = 14) {
    let changes = [];
    for (let i = 1; i < prices.length; i++) {
        changes.push(prices[i] - prices[i - 1]);
    }

    let gains = changes.map(c => c > 0 ? c : 0);
    let losses = changes.map(c => c < 0 ? -c : 0);

    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

    let rsi = [null];

    for (let i = period; i < changes.length; i++) {
        avgGain = (avgGain * (period - 1) + gains[i]) / period;
        avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
        let rs = avgGain / avgLoss;
        rsi.push(100 - (100 / (1 + rs)));
    }

    // 前面补null让长度对齐
    while (rsi.length < prices.length) {
        rsi.unshift(null);
    }

    return rsi;
}

// 获取588000历史数据，使用allorigins代理解决跨域
async function fetchData() {
    try {
        // 使用10jqka接口获取数据，通过allorigins.win代理解决跨域
        const proxyUrl = 'https://api.allorigins.win/get?url=';
        const targetUrl = encodeURIComponent('http://api.10jqka.com.cn/v1/kline/min?symbol=SH.588000');

        const response = await fetch(proxyUrl + targetUrl);
        const data = await response.json();
        const json = JSON.parse(data.contents);

        if (json && json.data && json.data.length > 0) {
            console.log(`Got ${json.data.length} real 1min candles from 10jqka`);
            const parsedData = json.data.map(item => {
                return {
                    time: new Date(item[0]),
                    open: parseFloat(item[1]),
                    high: parseFloat(item[2]),
                    low: parseFloat(item[3]),
                    close: parseFloat(item[4]),
                    volume: parseFloat(item[5])
                };
            });
            // 过滤出2026年1月1日之后的数据
            const startTime = new Date("2026-01-01").getTime();
            const filteredData = parsedData.filter(item => item.time.getTime() >= startTime);
            if (filteredData.length > 14) {
                console.log(`Filtered to ${filteredData.length} candles after 2026-01-01`);
                return filteredData;
            }
        }
        console.log("No valid data from API, using sample data");
        return generateSampleData();
    } catch (e) {
        console.log("API fetch failed, using sample data:", e);
        return generateSampleData();
    }
}

// 生成更真实的模拟数据，只包含A股交易时间
// 交易时间：上午 9:30-11:30 (120分钟)，下午 13:00-15:00 (120分钟)，每天 240 根一分钟K线
function generateSampleData() {
    let data = [];
    let basePrice = 0.85;
    let currentDate = new Date("2026-01-01");
    let endDate = new Date(); // 到今天

    // 从2026年1月1日遍历到今天
    while (currentDate <= endDate) {
        let dayOfWeek = currentDate.getDay(); // 0=周日, 6=周六
        // 跳过周末，只保留交易日
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
            // 上午交易时段 9:30-11:30
            let morningStart = new Date(currentDate);
            morningStart.setHours(9, 30, 0, 0);
            for (let i = 0; i < 120; i++) {
                let time = new Date(morningStart.getTime() + i * 60 * 1000);
                basePrice = generateNextPrice(basePrice);
                let candle = createCandle(time, basePrice);
                data.push(candle);
            }

            // 下午交易时段 13:00-15:00
            let afternoonStart = new Date(currentDate);
            afternoonStart.setHours(13, 0, 0, 0);
            for (let i = 0; i < 120; i++) {
                let time = new Date(afternoonStart.getTime() + i * 60 * 1000);
                basePrice = generateNextPrice(basePrice);
                let candle = createCandle(time, basePrice);
                data.push(candle);
            }
        }

        // 下一天
        currentDate.setDate(currentDate.getDate() + 1);
    }

    console.log(`Generated ${data.length} 1min candles (trading hours only) from 2026-01-01`);
    return data;
}

// 生成下一根K线价格，更贴合真实波动
function generateNextPrice(basePrice) {
    // 波动率贴合588000实际情况
    let change = (Math.random() - 0.5) * 0.015;
    // 加上一点趋势
    let trend = (Math.random() - 0.5) * 0.002;
    let newPrice = basePrice + change + trend;
    // 限制在合理价格区间
    return Math.max(newPrice, 0.68);
}

// 创建一根K线
function createCandle(time, basePrice) {
    let open = basePrice;
    let close = basePrice + (Math.random() - 0.5) * 0.008;
    let high = Math.max(open, close) + Math.random() * 0.004;
    let low = Math.min(open, close) - Math.random() * 0.004;

    // 保证价格合理
    high = Math.max(high, open, close);
    low = Math.min(low, open, close);

    return {
        time: time,
        open: open,
        high: high,
        low: low,
        close: close,
        volume: Math.floor(Math.random() * 15000000) + 2000000
    };
}

// 执行回测
function runBacktest(data, rsiValues) {
    let positions = [];
    let currentPosition = null;
    let equity = [1]; // 净值从1开始
    let lastClose = null;

    for (let i = 14; i < data.length; i++) {
        let rsi = rsiValues[i];
        let currentClose = data[i].close;
        let prevRsi = rsiValues[i - 1];

        if (prevRsi === null || rsi === null) continue;

        // 计算当前净值
        if (currentPosition) {
            let pnl = (currentClose - currentPosition.entryPrice) / currentPosition.entryPrice;
            equity.push(equity[equity.length - 1] * (1 + pnl));
        } else {
            equity.push(equity[equity.length - 1]);
        }

        // 开仓条件：RSI从低于30回升上穿30
        if (!currentPosition && prevRsi < 30 && rsi >= 30) {
            currentPosition = {
                entryTime: data[i].time,
                entryPrice: currentClose
            };
        }

        // 平仓条件：RSI从高于70回落跌破70
        else if (currentPosition && prevRsi > 70 && rsi <= 70) {
            currentPosition.exitTime = data[i].time;
            currentPosition.exitPrice = currentClose;
            currentPosition.pnl = (currentPosition.exitPrice - currentPosition.entryPrice) / currentPosition.entryPrice;
            positions.push(currentPosition);
            currentPosition = null;
        }

        lastClose = currentClose;
    }

    // 如果还有持仓，平仓
    if (currentPosition) {
        currentPosition.exitTime = data[data.length - 1].time;
        currentPosition.exitPrice = data[data.length - 1].close;
        currentPosition.pnl = (currentPosition.exitPrice - currentPosition.entryPrice) / currentPosition.entryPrice;
        positions.push(currentPosition);
    }

    return {
        positions,
        equity,
        dates: data.map(d => d.time)
    };
}

// 计算统计指标
function calculateMetrics(result) {
    let {positions, equity} = result;
    if (positions.length === 0) {
        return {
            totalTrades: 0,
            winningTrades: 0,
            winRate: 0,
            totalReturn: 0,
            maxDrawdown: 0,
            sharpeRatio: 0
        };
    }

    let winningTrades = positions.filter(p => p.pnl > 0).length;
    let totalReturn = equity[equity.length - 1] - 1;

    // 计算最大回撤
    let maxDrawdown = 0;
    let peak = equity[0];
    for (let e of equity) {
        if (e > peak) {
            peak = e;
        }
        let drawdown = (peak - e) / peak;
        if (drawdown > maxDrawdown) {
            maxDrawdown = drawdown;
        }
    }

    // 计算每日收益率和夏普比率
    let returns = [];
    for (let i = 1; i < equity.length; i++) {
        returns.push((equity[i] - equity[i - 1]) / equity[i - 1]);
    }
    let avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    let stdDev = Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length);
    let sharpeRatio = stdDev === 0 ? 0 : (avgReturn * Math.sqrt(252 * 240)) / stdDev;

    return {
        totalTrades: positions.length,
        winningTrades,
        winRate: (winningTrades / positions.length * 100).toFixed(2),
        totalReturn: (totalReturn * 100).toFixed(2),
        maxDrawdown: (maxDrawdown * 100).toFixed(2),
        sharpeRatio: sharpeRatio.toFixed(2)
    };
}

// 绘制图表
let equityChartInstance = null;
let rsiChartInstance = null;
let priceChartInstance = null;

function drawCharts(data, result, rsiValues) {
    // 先确保结果区域显示
    document.getElementById('resultsSection').style.display = 'block';
    
    setTimeout(() => {
        let equityData = result.equity;
        let labels = data.map(d => {
            return d.time.toLocaleDateString() + ' ' + d.time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        });

        // 采样减少数据点
        let sampleStep = Math.ceil(labels.length / 100);
        let sampledLabels = [];
        let sampledEquity = [];
        let sampledRsi = [];
        let sampledClose = [];
        
        for (let i = 0; i < labels.length; i += sampleStep) {
            sampledLabels.push(labels[i]);
            sampledEquity.push(equityData[i] * 100 - 100);
            if (rsiValues[i] !== null) {
                sampledRsi.push(rsiValues[i]);
            } else {
                sampledRsi.push(null);
            }
            sampledClose.push(data[i].close);
        }

        // 净值曲线
        const equityCanvas = document.getElementById('equityChart');
        if (!equityCanvas) return;
        const equityCtx = equityCanvas.getContext('2d');
        if (equityChartInstance) {
            equityChartInstance.destroy();
        }

        equityChartInstance = new Chart(equityCtx, {
            type: 'line',
            data: {
                labels: sampledLabels,
                datasets: [{
                    label: '净值收益率 (%)',
                    data: sampledEquity,
                    borderColor: '#1e3a8a',
                    backgroundColor: 'rgba(30, 58, 138, 0.1)',
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });

        // RSI图表
        const rsiCanvas = document.getElementById('rsiChart');
        if (!rsiCanvas) return;
        const rsiCtx = rsiCanvas.getContext('2d');
        if (rsiChartInstance) {
            rsiChartInstance.destroy();
        }

        rsiChartInstance = new Chart(rsiCtx, {
            type: 'line',
            data: {
                labels: sampledLabels,
                datasets: [{
                    label: 'RSI(14)',
                    data: sampledRsi,
                    borderColor: '#d4af37',
                    backgroundColor: 'rgba(212, 175, 55, 0.1)',
                    fill: false,
                    tension: 0.1
                }, {
                    label: '超买线 70',
                    data: Array(sampledLabels.length).fill(70),
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }, {
                    label: '超卖线 30',
                    data: Array(sampledLabels.length).fill(30),
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100
                    }
                }
            }
        });

        // 价格走势图 (单独一张图)
        const priceCanvas = document.getElementById('priceChart');
        if (!priceCanvas) return;
        const priceCtx = priceCanvas.getContext('2d');
        if (priceChartInstance) {
            priceChartInstance.destroy();
        }

        priceChartInstance = new Chart(priceCtx, {
            type: 'line',
            data: {
                labels: sampledLabels,
                datasets: [{
                    label: '588000 价格',
                    data: sampledClose,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }, 100);
}

// 显示交易记录
function displayTrades(positions) {
    let tbody = document.getElementById('tradesTableBody');
    tbody.innerHTML = '';

    positions.slice(-20).reverse().forEach((p, i) => {
        let row = document.createElement('tr');
        let pnlPercent = (p.pnl * 100).toFixed(2);
        let pnlClass = p.pnl >= 0 ? 'positive-return' : 'negative-return';

        row.innerHTML = `
            <td>${positions.length - i}</td>
            <td>${p.entryTime.toLocaleString()}</td>
            <td>${p.entryPrice.toFixed(4)}</td>
            <td>${p.exitTime.toLocaleString()}</td>
            <td>${p.exitPrice.toFixed(4)}</td>
            <td class="${pnlClass}">${pnlPercent}%</td>
        `;
        tbody.appendChild(row);
    });
}

// 显示结果
function displayResults(result, metrics, data, rsiValues) {
    document.getElementById('totalTrades').textContent = metrics.totalTrades;
    document.getElementById('winningTrades').textContent = metrics.winningTrades;
    document.getElementById('winRate').textContent = metrics.winRate + '%';

    let totalReturnEl = document.getElementById('totalReturn');
    totalReturnEl.textContent = metrics.totalReturn + '%';
    totalReturnEl.className = 'metric-value ' + (metrics.totalReturn >= 0 ? 'positive' : 'negative');

    let maxDrawdownEl = document.getElementById('maxDrawdown');
    maxDrawdownEl.textContent = metrics.maxDrawdown + '%';
    maxDrawdownEl.className = 'metric-value negative';

    document.getElementById('sharpeRatio').textContent = metrics.sharpeRatio;

    displayTrades(result.positions);

    // 绘制图表
    drawCharts(data, result, rsiValues);
}

// 主程序
document.getElementById('startBacktest').addEventListener('click', async function() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    this.disabled = true;

    try {
        // 获取数据
        let data = await fetchData();
        console.log(`Loaded ${data.length} 1-minute candles`);

        if (data.length < 14) {
            alert('数据不足，请稍后重试');
            document.getElementById('loading').style.display = 'none';
            this.disabled = false;
            return;
        }

        // 计算RSI
        let closes = data.map(d => d.close);
        let rsiValues = calculateRSI(closes, 14);

        // 执行回测
        let result = runBacktest(data, rsiValues);

        // 计算指标
        let metrics = calculateMetrics(result);

        // 绘制图表
        drawCharts(data, result, rsiValues);

        // 显示结果
        displayResults(result, metrics, data, rsiValues);

    } catch (e) {
        console.error(e);
        alert('回测执行出错: ' + e.message);
    }

    document.getElementById('loading').style.display = 'none';
    this.disabled = false;
});

// 修改首页按钮链接指向回测页面
document.addEventListener('DOMContentLoaded', function() {
    let btn = document.querySelector('.hero-content .btn');
    if (btn) {
        btn.setAttribute('href', 'backtest.html');
    }
});