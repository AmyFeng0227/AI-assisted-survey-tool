@echo off
echo ========================================
echo Running Multiple Evaluation Tests
echo ========================================
echo.

echo Test 1: Small chunks (10 sentences, 2 overlap)
python run_evaluation.py 10 2
echo.

echo ========================================
echo Test 2: Medium chunks (15 sentences, 3 overlap)
python run_evaluation.py 15 3
echo.

echo ========================================
echo Test 3: Large chunks (20 sentences, 2 overlap)
python run_evaluation.py 20 2
echo.

echo ========================================
echo Test 4: Large chunks with more overlap (20 sentences, 5 overlap)
python run_evaluation.py 20 5
echo.

echo ========================================
echo All tests complete! Check evaluation/evaluation_results.jsonl for results.
echo ========================================
pause 