async function fetchLoanData() {
    try {
        const response = await fetch('http://localhost:5004/loans-total-data');
        if (!response.ok) throw new Error('Failed to fetch loan data');
        const data = await response.json();
        console.log('Received data:', data); // Log the received data
        
        const loanDataTableBody = document.getElementById('loanDataTableBody');
        loanDataTableBody.innerHTML = '';
        
        // Check if data has the expected structure
        if (data && data.data && Array.isArray(data.data)) {
            // Update table header to include book_id column
            const tableHeader = document.querySelector('#loanDataTable thead tr');
            if (tableHeader && tableHeader.children.length === 2) {
                tableHeader.innerHTML = `
                    <th>Month</th>
                    <th>Book ID</th>
                    <th>Total Loans</th>
                `;
            }
            
            // Store the data globally for pagination
            window.loanData = data.data;
            
            // Create pagination controls if more than 10 items
            if (data.data.length > 10) {
                createPagination(data.data.length, 'loanPagination', displayLoanPage);
            } else {
                // If pagination container exists, clear it
                const paginationContainer = document.getElementById('loanPagination');
                if (paginationContainer) {
                    paginationContainer.innerHTML = '';
                }
                
                // Display all data if 10 or fewer items
                displayLoanData(data.data, 0, 10);
            }
        } else {
            loanDataTableBody.innerHTML = '<tr><td colspan="3">No data available or invalid format</td></tr>';
            console.warn('Unexpected data format:', data);
        }
    } catch (error) {
        console.error('Error fetching loan data:', error);
        alert('Failed to fetch loan data. Please check the backend server.');
    }
}

// Function to display loan data for a specific page
function displayLoanPage(page) {
    const startIndex = (page - 1) * 10;
    const endIndex = startIndex + 10;
    displayLoanData(window.loanData, startIndex, endIndex);
}

// Function to display loan data with start and end indices
function displayLoanData(data, startIndex, endIndex) {
    const loanDataTableBody = document.getElementById('loanDataTableBody');
    loanDataTableBody.innerHTML = '';
    
    const pageData = data.slice(startIndex, endIndex);
    
    if (pageData.length === 0) {
        loanDataTableBody.innerHTML = '<tr><td colspan="3">No data available for this page</td></tr>';
        return;
    }
    
    pageData.forEach(entry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${entry.date ? new Date(entry.date).toLocaleDateString() : 'N/A'}</td>
            <td>${entry.book_id || 'N/A'}</td>
            <td>${entry.borrowed_count || 0}</td>
        `;
        loanDataTableBody.appendChild(row);
    });
}

// Function to create pagination controls
function createPagination(totalItems, containerId, callback) {
    const totalPages = Math.ceil(totalItems / 10);
    
    // Create pagination container if it doesn't exist
    let paginationContainer = document.getElementById(containerId);
    if (!paginationContainer) {
        // Find the table container and append pagination after it
        const tableContainer = document.getElementById('loanDataTable').parentNode;
        paginationContainer = document.createElement('div');
        paginationContainer.id = containerId;
        paginationContainer.className = 'pagination';
        tableContainer.appendChild(paginationContainer);
    }
    
    // Function to update pagination UI
    function updatePaginationUI(currentPage) {
        paginationContainer.innerHTML = '';
        
        // Previous button
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.className = 'pagination-btn';
        prevButton.onclick = function() {
            if (currentPage > 1) {
                changePage(currentPage - 1);
            }
        };
        paginationContainer.appendChild(prevButton);
        
        // Calculate which page buttons to show (always show 5 if possible)
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        // Adjust start page if we're near the end
        if (endPage - startPage < 4 && totalPages > 5) {
            startPage = Math.max(1, endPage - 4);
        }
        
        // Page buttons
        for (let i = startPage; i <= endPage; i++) {
            const pageButton = document.createElement('button');
            pageButton.textContent = i;
            pageButton.className = 'pagination-btn' + (i === currentPage ? ' active' : '');
            pageButton.onclick = function() {
                changePage(i);
            };
            paginationContainer.appendChild(pageButton);
        }
        
        // Next button
        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.className = 'pagination-btn';
        nextButton.onclick = function() {
            if (currentPage < totalPages) {
                changePage(currentPage + 1);
            }
        };
        paginationContainer.appendChild(nextButton);
    }
    
    // Function to change page
    function changePage(page) {
        paginationContainer.setAttribute('data-current-page', page);
        updatePaginationUI(page);
        callback(page);
    }
    
    // Initialize with page 1
    paginationContainer.setAttribute('data-current-page', 1);
    updatePaginationUI(1);
    callback(1);
}

async function fetchPrediction() {
    try {
        const predictDate = document.getElementById('predictDate').value;
        const isPeakSeason = document.getElementById('isPeakSeason').checked ? 1 : 0;
        const isLowSeason = document.getElementById('isLowSeason').checked ? 1 : 0;
        const modelNo = parseInt(document.getElementById('modelNo').value);

        // Log request data untuk debugging
        console.log('Sending prediction request with data:', {
            date: predictDate,
            is_peak_season: isPeakSeason,
            is_low_season: isLowSeason,
            model_no: modelNo
        });

        // Mengubah ke metode GET dengan query parameters
        const queryParams = new URLSearchParams({
            date: predictDate,
            is_peak_season: isPeakSeason,
            is_low_season: isLowSeason
        });
        
        const url = `http://localhost:5004/predict/${modelNo}?${queryParams.toString()}`;
        console.log('Request URL:', url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) throw new Error('Failed to fetch prediction');
        
        const responseData = await response.json();
        console.log('Prediction data received:', responseData);

        // Memeriksa struktur response sesuai dengan format baru
        if (responseData.success && responseData.data) {
            const predictTableBody = document.getElementById('predictTableBody');
            predictTableBody.innerHTML = '';
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${predictDate}</td>
                <td>${responseData.data.prediction}</td>
            `;
            predictTableBody.appendChild(row);
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Error fetching prediction:', error);
        alert('Failed to fetch prediction. Please check the backend server.');
    }
}

async function fetchModelErrors() {
    try {
        console.log('Fetching model error metrics...');
        
        const response = await fetch('http://localhost:5004/evaluate', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) throw new Error('Failed to fetch model error metrics');
        
        const responseData = await response.json();
        console.log('Model error metrics received:', responseData);

        if (responseData.success && responseData.data) {
            const errorTableBody = document.getElementById('errorTableBody');
            errorTableBody.innerHTML = '';
            
            // Loop through each model's metrics
            for (const [modelKey, metrics] of Object.entries(responseData.data)) {
                const row = document.createElement('tr');
                
                // Extract model number from the key (e.g., "model_1" -> "1")
                const modelNumber = modelKey.split('_')[1];
                
                // Check if there's an error for this model
                if (metrics.error) {
                    row.innerHTML = `
                        <td>Model ${modelNumber}</td>
                        <td colspan="4">Error: ${metrics.error}</td>
                    `;
                } else {
                    // Menggunakan r2_score jika tersedia, jika tidak gunakan r2 sebagai fallback
                    const r2Value = metrics.r2_score !== undefined ? metrics.r2_score : metrics.r2;
                    
                    row.innerHTML = `
                        <td>Model ${modelNumber}</td>
                        <td>${typeof metrics.mse === 'number' ? metrics.mse.toFixed(4) : metrics.mse}</td>
                        <td>${typeof metrics.rmse === 'number' ? metrics.rmse.toFixed(4) : metrics.rmse}</td>
                        <td>${typeof metrics.mae === 'number' ? metrics.mae.toFixed(4) : metrics.mae}</td>
                        <td>${typeof r2Value === 'number' ? r2Value.toFixed(4) : r2Value}</td>
                    `;
                }
                
                errorTableBody.appendChild(row);
            }
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Error fetching model error metrics:', error);
        alert('Failed to fetch model error metrics. Please check the backend server.');
    }
}