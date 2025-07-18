<?php
// === Path to local JSON file ===
$jsonPath = __DIR__ . '/hindu-main-news.json';

// === Accept GET Parameters ===
$dateParam = $_GET['date'] ?? null;       // e.g., 17Jul2025
$keywordParam = $_GET['keyword'] ?? null; // e.g., Indore, Ram Mandir

// === Check if JSON file exists ===
if (!file_exists($jsonPath)) {
    http_response_code(404);
    echo json_encode(['error' => 'JSON file not found']);
    exit;
}

// === Read and decode JSON ===
$json = file_get_contents($jsonPath);
$data = json_decode($json, true);

// === Validate JSON ===
if (!$data || !is_array($data)) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to parse JSON']);
    exit;
}

// === Helper: Normalize Date format like 17Jul2025 ===
function normalizeDate($dateString) {
    $ts = strtotime($dateString);
    return $ts ? date('dMY', $ts) : null;
}

// === Filter Logic ===
$filtered = array_filter($data, function($item) use ($dateParam, $keywordParam) {
    $matchDate = true;
    $matchKeyword = true;

    // Match by date
    if ($dateParam) {
        $itemDate = normalizeDate($item['published'] ?? '');
        $matchDate = ($itemDate === $dateParam);
    }

    // Match by keyword in content (case-insensitive)
    if ($keywordParam) {
        $content = $item['content'] ?? '';
        $matchKeyword = stripos($content, $keywordParam) !== false;
    }

    return $matchDate && $matchKeyword;
});

// === Output JSON response ===
header('Content-Type: application/json');
echo json_encode(array_values($filtered), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
