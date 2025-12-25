# Test script for semantic memory functionality
# Tests if summaries are stored in Qdrant and can be retrieved via semantic search

$API_BASE_URL = "http://localhost:8006"
$userId = "test_user_$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Semantic Memory Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create a conversation
Write-Host "[1/5] Creating conversation..." -ForegroundColor Yellow
$createResponse = Invoke-RestMethod -Uri "$API_BASE_URL/api/conversations" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        user_id = $userId
        content = "I'm building a Python web application using FastAPI. I need help with database design."
    } | ConvertTo-Json)

$conversationId = $createResponse.conversation.id
Write-Host "    Conversation ID: $conversationId" -ForegroundColor Green
Write-Host "    First response: $($createResponse.message.response.Substring(0, [Math]::Min(100, $createResponse.message.response.Length)))..." -ForegroundColor Gray
Write-Host ""

# Step 2: Send multiple messages to trigger summary creation (every 5 turns)
Write-Host "[2/5] Sending messages to trigger summary creation..." -ForegroundColor Yellow
$messages = @(
    "I want to use PostgreSQL as my database. What's the best way to structure my tables?",
    "I'm storing user data, product information, and order history.",
    "Should I use foreign keys or just store IDs?",
    "What about indexing strategies for fast queries?",
    "Actually, I also need to track user sessions and analytics."
)

$turnNumber = 2
foreach ($message in $messages) {
    Write-Host "    [Turn $turnNumber] Sending: $($message.Substring(0, [Math]::Min(50, $message.Length)))..." -ForegroundColor Gray
    try {
        $response = Invoke-RestMethod -Uri "$API_BASE_URL/api/conversations/$conversationId/messages" `
            -Method POST `
            -ContentType "application/json" `
            -Body (@{
                user_id = $userId
                content = $message
            } | ConvertTo-Json)
        Write-Host "        Response tokens: $($response.tokens_used)" -ForegroundColor DarkGray
        Start-Sleep -Milliseconds 500
        $turnNumber++
    } catch {
        Write-Host "        ERROR: $_" -ForegroundColor Red
    }
}
Write-Host ""

# Step 3: Check memory state (should have summaries after turn 5)
Write-Host "[3/5] Checking memory state..." -ForegroundColor Yellow
try {
    $memoryResponse = Invoke-RestMethod -Uri "$API_BASE_URL/api/conversations/$conversationId/memory" `
        -Method GET
    
    Write-Host "    Total turns: $($memoryResponse.total_turns)" -ForegroundColor Green
    Write-Host "    Short-term turns: $($memoryResponse.short_term_turns)" -ForegroundColor Green
    Write-Host "    Long-term summaries: $($memoryResponse.long_term_summaries)" -ForegroundColor Green
    Write-Host "    Semantic results: $($memoryResponse.semantic_results)" -ForegroundColor Green
    Write-Host "    Context tokens: $($memoryResponse.total_context_tokens)" -ForegroundColor Green
    
    if ($memoryResponse.summaries -and $memoryResponse.summaries.Count -gt 0) {
        Write-Host "    Summaries found: $($memoryResponse.summaries.Count)" -ForegroundColor Green
        foreach ($summary in $memoryResponse.summaries) {
            Write-Host "        - Turns $($summary.turn_range[0])-$($summary.turn_range[1]): $($summary.summary.Substring(0, [Math]::Min(80, $summary.summary.Length)))..." -ForegroundColor DarkGray
        }
    } else {
        Write-Host "    WARNING: No summaries found yet. Summaries are created every 5 turns." -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Step 4: Create a second conversation with related topic to test semantic search
Write-Host "[4/5] Creating second conversation for semantic search test..." -ForegroundColor Yellow
$createResponse2 = Invoke-RestMethod -Uri "$API_BASE_URL/api/conversations" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        user_id = $userId
        content = "I need help with database optimization for my FastAPI app."
    } | ConvertTo-Json)

$conversationId2 = $createResponse2.conversation.id
Write-Host "    Second Conversation ID: $conversationId2" -ForegroundColor Green
Write-Host ""

# Step 5: Send a query that should trigger semantic search
Write-Host "[5/5] Sending query that should trigger semantic search..." -ForegroundColor Yellow
try {
    $queryResponse = Invoke-RestMethod -Uri "$API_BASE_URL/api/conversations/$conversationId2/messages" `
        -Method POST `
        -ContentType "application/json" `
        -Body (@{
            user_id = $userId
            content = "What did we discuss about PostgreSQL table structure?"
        } | ConvertTo-Json)
    
    Write-Host "    Query response: $($queryResponse.response.Substring(0, [Math]::Min(200, $queryResponse.response.Length)))..." -ForegroundColor Green
    Write-Host "    Tokens used: $($queryResponse.tokens_used)" -ForegroundColor Green
    Write-Host "    Context tokens: $($queryResponse.context_tokens)" -ForegroundColor Green
    
    # Check if semantic memory was used (context_tokens should be higher if semantic results were included)
    if ($queryResponse.context_tokens -gt 100) {
        Write-Host "    [OK] Semantic memory likely used (high context tokens)" -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Semantic memory may not have been used (low context tokens)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ERROR: $_" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Conversation 1 ID: $conversationId" -ForegroundColor White
Write-Host "Conversation 2 ID: $conversationId2" -ForegroundColor White
Write-Host ""
Write-Host "To verify semantic memory:" -ForegroundColor Yellow
Write-Host "1. Check if summaries were created (should be > 0 after 5+ turns)" -ForegroundColor White
Write-Host "2. Check if semantic_results > 0 when querying related topics" -ForegroundColor White
Write-Host "3. Check Qdrant directly: docker exec -it conversational-ai-qdrant qdrant-cli" -ForegroundColor White
Write-Host ""
Write-Host ""

