

import google.generativeai as genai
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionAnalyzer:
    
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer with Gemini API key."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Gemini 2.5 model initialized successfully")
    
    def analyze_patterns(self, patterns: Dict[str, Any], summary_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns using Gemini and identify suspicious threads."""
        
        analysis_results = {}
        
        # Prioritize pattern types for faster initial response
        priority_patterns = ['frequent_pairs', 'round_amounts', 'high_activity_periods']
        other_patterns = [pt for pt in patterns.keys() if pt not in priority_patterns]
        
        # Analyze priority patterns first (most likely to contain suspicious activity)
        for pattern_type in priority_patterns:
            if pattern_type in patterns and patterns[pattern_type]:
                try:
                    analysis = self._analyze_pattern_type_optimized(pattern_type, patterns[pattern_type], summary_stats)
                    analysis_results[pattern_type] = analysis
                    logger.info(f"Completed priority analysis for pattern type: {pattern_type}")
                except Exception as e:
                    logger.error(f"Error analyzing priority pattern {pattern_type}: {e}")
                    analysis_results[pattern_type] = {
                        'error': str(e),
                        'threads': [],
                        'risk_level': 'unknown'
                    }
        
        # Analyze remaining patterns with smaller data chunks
        for pattern_type in other_patterns:
            if pattern_type in patterns and patterns[pattern_type]:
                try:
                    analysis = self._analyze_pattern_type_optimized(pattern_type, patterns[pattern_type], summary_stats)
                    analysis_results[pattern_type] = analysis
                    logger.info(f"Completed analysis for pattern type: {pattern_type}")
                except Exception as e:
                    logger.error(f"Error analyzing pattern {pattern_type}: {e}")
                    analysis_results[pattern_type] = {
                        'error': str(e),
                        'threads': [],
                        'risk_level': 'unknown'
                    }
        
        # Generate overall assessment
        overall_analysis = self._generate_overall_analysis(analysis_results, summary_stats)
        analysis_results['overall_assessment'] = overall_analysis
        
        return analysis_results
    
    def _analyze_pattern_type_optimized(self, pattern_type: str, pattern_data: List[Dict], summary_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Balanced analysis with improved accuracy while maintaining performance."""
        
        # Use more data for better accuracy, but still limit for performance
        max_items = 25 if pattern_type in ['frequent_pairs', 'round_amounts'] else 20
        limited_data = pattern_data[:max_items]
        
        # Create enhanced prompt for better accuracy
        prompt = self._create_enhanced_analysis_prompt(pattern_type, limited_data, summary_stats)
        
        try:
            # Use balanced generation settings for better accuracy
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=1500,  # Increased for more detailed analysis
                temperature=0.2,  # Lower temperature for more consistent, accurate responses
                top_p=0.9,  # Higher top_p for better quality
                top_k=40  # Higher top_k for more diverse but accurate responses
            )
            
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            # Parse the response
            analysis_text = response.text
            
            # Extract structured information from the response
            structured_analysis = self._parse_llm_response(analysis_text, pattern_type)
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error in enhanced LLM analysis: {e}")
            # Fallback to basic analysis
            return self._create_fallback_analysis(pattern_type, limited_data)
    
    def _analyze_pattern_type(self, pattern_type: str, pattern_data: List[Dict], summary_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific pattern type using Gemini."""
        
        # Create context-specific prompts for different pattern types
        prompt = self._create_analysis_prompt(pattern_type, pattern_data, summary_stats)
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse the response
            analysis_text = response.text
            
            # Extract structured information from the response
            structured_analysis = self._parse_llm_response(analysis_text, pattern_type)
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            raise
    
    def _create_analysis_prompt(self, pattern_type: str, pattern_data: List[Dict], summary_stats: Dict[str, Any]) -> str:
        """Create context-specific prompts for different pattern types."""
        
        base_context = f"""
        You are a financial transaction analyst specializing in detecting suspicious patterns and money laundering activities.
        
        Dataset Overview:
        - Total transactions: {summary_stats.get('total_transactions', 0)}
        - Unique users: {summary_stats.get('unique_users', 0)}
        - Total amount: ${summary_stats.get('total_amount', 0):,.2f}
        - Date range: {summary_stats.get('date_range', {}).get('start', 'Unknown')} to {summary_stats.get('date_range', {}).get('end', 'Unknown')}
        
        """
        
        if pattern_type == 'frequent_pairs':
            prompt = base_context + f"""
            PATTERN TYPE: Frequent User Pairs
            
            Analyze the following frequent transaction pairs for suspicious activity:
            {json.dumps(pattern_data[:10], indent=2, default=str)}
            
            Focus on:
            1. Unusually high frequency between specific users
            2. Round number amounts that might indicate structuring
            3. Rapid back-and-forth transactions (potential layering)
            4. Consistent amounts that might indicate regular payments or suspicious activity
            
            Provide analysis in this JSON format:
            {{
                "threads": [
                    {{
                        "thread_id": "unique_identifier",
                        "description": "Brief description of the suspicious pattern",
                        "participants": ["user1", "user2"],
                        "risk_level": "high|medium|low",
                        "evidence": ["specific evidence points"],
                        "transactions_involved": ["transaction_ids"],
                        "potential_violation": "type of potential violation"
                    }}
                ],
                "risk_level": "overall risk level for this pattern type",
                "summary": "brief summary of findings"
            }}
            """
        
        elif pattern_type == 'round_amounts':
            prompt = base_context + f"""
            PATTERN TYPE: Round Amount Transactions
            
            Analyze these round number transactions for potential structuring or suspicious activity:
            {json.dumps(pattern_data[:20], indent=2, default=str)}
            
            Focus on:
            1. Transactions just under reporting thresholds
            2. Multiple round amounts from same users
            3. Patterns that suggest deliberate structuring
            4. Unusual frequency of round amounts
            
            Provide analysis in the same JSON format as above.
            """
        
        elif pattern_type == 'high_activity_periods':
            prompt = base_context + f"""
            PATTERN TYPE: High Activity Periods
            
            Analyze these high-activity time periods for suspicious patterns:
            {json.dumps(pattern_data[:5], indent=2, default=str)}
            
            Focus on:
            1. Unusual spikes in transaction volume
            2. Coordinated activity across multiple users
            3. Off-hours activity that might indicate automation
            4. Concentration of high-value transactions
            
            Provide analysis in the same JSON format as above.
            """
        
        elif pattern_type == 'repeated_amounts':
            prompt = base_context + f"""
            PATTERN TYPE: Repeated Amount Patterns
            
            Analyze these repeated transaction amounts:
            {json.dumps(pattern_data[:15], indent=2, default=str)}
            
            Focus on:
            1. Exact amounts repeated across different users
            2. Potential coordination or automation
            3. Amounts that might indicate specific services or products
            4. Suspicious uniformity in transaction amounts
            
            Provide analysis in the same JSON format as above.
            """
        
        elif pattern_type == 'quick_successive':
            prompt = base_context + f"""
            PATTERN TYPE: Quick Successive Transactions
            
            Analyze these rapid successive transactions:
            {json.dumps(pattern_data[:20], indent=2, default=str)}
            
            Focus on:
            1. Potential automated or scripted transactions
            2. Rapid movement of funds (layering)
            3. Test transactions followed by larger amounts
            4. Unusual speed that might indicate non-human activity
            
            Provide analysis in the same JSON format as above.
            """
        
        else:
            prompt = base_context + f"""
            PATTERN TYPE: {pattern_type.title()}
            
            Analyze this transaction pattern data:
            {json.dumps(pattern_data[:10], indent=2, default=str)}
            
            Provide a general analysis focusing on any suspicious indicators.
            Use the same JSON format as specified above.
            """
        
        return prompt
    
    def _create_enhanced_analysis_prompt(self, pattern_type: str, pattern_data: List[Dict], summary_stats: Dict[str, Any]) -> str:
        """Create enhanced prompts for better accuracy and detailed analysis."""
        
        base_context = f"""
        You are an expert financial crime analyst with 15+ years of experience in AML (Anti-Money Laundering) and fraud detection.
        
        DATASET CONTEXT:
        - Total transactions: {summary_stats.get('total_transactions', 0):,}
        - Unique users: {summary_stats.get('unique_users', 0):,}
        - Total amount: ${summary_stats.get('total_amount', 0):,.2f}
        - Average transaction: ${summary_stats.get('average_amount', 0):,.2f}
        - Date range: {summary_stats.get('date_range', {}).get('start', 'Unknown')} to {summary_stats.get('date_range', {}).get('end', 'Unknown')}
        
        ANALYSIS REQUIREMENTS:
        - Focus on suspicious patterns that indicate money laundering, fraud, or other financial crimes
        - Consider regulatory thresholds (e.g., $10,000 reporting requirements)
        - Look for structuring, layering, and integration techniques
        - Identify unusual timing, amounts, and user behaviors
        - Provide specific evidence and risk assessments
        
        """
        
        if pattern_type == 'frequent_pairs':
            prompt = base_context + f"""
            PATTERN: FREQUENT USER PAIRS ANALYSIS
            
            Analyze these frequent transaction pairs for suspicious activity:
            {json.dumps(pattern_data, indent=2, default=str)}
            
            CRITICAL ANALYSIS POINTS:
            1. **Frequency Analysis**: Look for unusually high transaction counts between specific users
            2. **Amount Patterns**: Identify round numbers, amounts just under thresholds, or suspiciously consistent amounts
            3. **Timing Analysis**: Check for rapid back-and-forth transactions, unusual timing patterns
            4. **Behavioral Indicators**: Look for potential layering, structuring, or coordination
            5. **Risk Assessment**: Consider the total volume, frequency, and pattern consistency
            
            SUSPICIOUS INDICATORS TO IDENTIFY:
            - Transactions just under $10,000 (structuring)
            - Rapid back-and-forth transfers (layering)
            - Round number amounts (potential automation)
            - High frequency with consistent amounts
            - Unusual timing (off-hours, weekends)
            - Multiple users with similar patterns
            
            Provide detailed analysis in this JSON format:
            {{
                "threads": [
                    {{
                        "thread_id": "unique_identifier",
                        "description": "Detailed description of the suspicious pattern with specific evidence",
                        "participants": ["user1", "user2"],
                        "risk_level": "high|medium|low",
                        "evidence": [
                            "Specific evidence point 1 with numbers/amounts",
                            "Specific evidence point 2 with timing details",
                            "Specific evidence point 3 with behavioral indicators"
                        ],
                        "transactions_involved": ["transaction_ids"],
                        "potential_violation": "Specific type of potential violation (e.g., 'Structuring to avoid reporting requirements', 'Potential layering scheme')",
                        "confidence_score": 0.85,
                        "recommended_action": "Specific recommended action"
                    }}
                ],
                "risk_level": "overall risk level for this pattern type",
                "summary": "Comprehensive summary of findings with key statistics",
                "key_insights": ["Key insight 1", "Key insight 2", "Key insight 3"]
            }}
            """
        
        elif pattern_type == 'round_amounts':
            prompt = base_context + f"""
            PATTERN: ROUND AMOUNT TRANSACTIONS ANALYSIS
            
            Analyze these round number transactions for potential structuring or suspicious activity:
            {json.dumps(pattern_data, indent=2, default=str)}
            
            CRITICAL ANALYSIS POINTS:
            1. **Threshold Analysis**: Focus on amounts just under reporting thresholds ($9,999, $4,999, etc.)
            2. **Frequency Patterns**: Look for repeated round amounts from same users
            3. **Structuring Indicators**: Identify potential deliberate structuring to avoid detection
            4. **User Behavior**: Analyze if users consistently use round amounts
            5. **Timing Patterns**: Check for coordinated timing of round amount transactions
            
            SUSPICIOUS INDICATORS TO IDENTIFY:
            - Multiple transactions just under $10,000
            - Consistent round amounts (e.g., $5,000, $10,000, $15,000)
            - Same users making multiple round amount transactions
            - Round amounts combined with other suspicious patterns
            - Unusual frequency of round amounts in the dataset
            
            Provide detailed analysis in the same JSON format as above.
            """
        
        elif pattern_type == 'high_activity_periods':
            prompt = base_context + f"""
            PATTERN: HIGH ACTIVITY PERIODS ANALYSIS
            
            Analyze these high-activity time periods for suspicious patterns:
            {json.dumps(pattern_data, indent=2, default=str)}
            
            CRITICAL ANALYSIS POINTS:
            1. **Volume Spikes**: Identify unusual spikes in transaction volume
            2. **Coordinated Activity**: Look for coordinated activity across multiple users
            3. **Timing Analysis**: Check for off-hours activity that might indicate automation
            4. **Amount Concentration**: Analyze concentration of high-value transactions
            5. **User Behavior**: Identify unusual user behavior during these periods
            
            SUSPICIOUS INDICATORS TO IDENTIFY:
            - Unusual spikes in transaction volume
            - Coordinated activity across multiple users
            - Off-hours activity (late night, early morning)
            - Concentration of high-value transactions
            - Rapid succession of transactions
            - Unusual user behavior patterns
            
            Provide detailed analysis in the same JSON format as above.
            """
        
        elif pattern_type == 'repeated_amounts':
            prompt = base_context + f"""
            PATTERN: REPEATED AMOUNT PATTERNS ANALYSIS
            
            Analyze these repeated transaction amounts:
            {json.dumps(pattern_data, indent=2, default=str)}
            
            CRITICAL ANALYSIS POINTS:
            1. **Exact Amount Repetition**: Look for exact amounts repeated across different users
            2. **Coordination Indicators**: Identify potential coordination or automation
            3. **Service/Product Indicators**: Determine if amounts indicate specific services or products
            4. **Uniformity Analysis**: Check for suspicious uniformity in transaction amounts
            5. **User Patterns**: Analyze user behavior around repeated amounts
            
            SUSPICIOUS INDICATORS TO IDENTIFY:
            - Exact amounts repeated across different users
            - Potential coordination or automation
            - Amounts that might indicate specific services or products
            - Suspicious uniformity in transaction amounts
            - Unusual frequency of specific amounts
            
            Provide detailed analysis in the same JSON format as above.
            """
        
        elif pattern_type == 'quick_successive':
            prompt = base_context + f"""
            PATTERN: QUICK SUCCESSIVE TRANSACTIONS ANALYSIS
            
            Analyze these rapid successive transactions:
            {json.dumps(pattern_data, indent=2, default=str)}
            
            CRITICAL ANALYSIS POINTS:
            1. **Speed Analysis**: Identify potential automated or scripted transactions
            2. **Layering Indicators**: Look for rapid movement of funds (layering)
            3. **Test Transactions**: Check for test transactions followed by larger amounts
            4. **Timing Patterns**: Analyze unusual speed that might indicate non-human activity
            5. **User Behavior**: Identify unusual user behavior patterns
            
            SUSPICIOUS INDICATORS TO IDENTIFY:
            - Potential automated or scripted transactions
            - Rapid movement of funds (layering)
            - Test transactions followed by larger amounts
            - Unusual speed that might indicate non-human activity
            - Coordinated rapid transactions
            
            Provide detailed analysis in the same JSON format as above.
            """
        
        else:
            prompt = base_context + f"""
            PATTERN: {pattern_type.upper().replace('_', ' ')} ANALYSIS
            
            Analyze this transaction pattern data:
            {json.dumps(pattern_data, indent=2, default=str)}
            
            Focus on any suspicious indicators and provide detailed analysis.
            Use the same JSON format as specified above.
            """
        
        return prompt
    
    def _create_optimized_analysis_prompt(self, pattern_type: str, pattern_data: List[Dict], summary_stats: Dict[str, Any]) -> str:
        """Create optimized, shorter prompts for faster processing."""
        
        base_context = f"""
        Financial transaction analyst. Dataset: {summary_stats.get('total_transactions', 0)} transactions, {summary_stats.get('unique_users', 0)} users.
        
        """
        
        if pattern_type == 'frequent_pairs':
            prompt = base_context + f"""
            Analyze these frequent user pairs for suspicious activity:
            {json.dumps(pattern_data[:8], indent=2, default=str)}
            
            Focus on: high frequency, round amounts, rapid transactions.
            
            Return JSON:
            {{
                "threads": [{{"thread_id": "id", "description": "brief", "participants": ["user1", "user2"], "risk_level": "high|medium|low", "evidence": ["evidence"], "transactions_involved": ["ids"], "potential_violation": "type"}}],
                "risk_level": "overall_risk",
                "summary": "brief_summary"
            }}
            """
        
        elif pattern_type == 'round_amounts':
            prompt = base_context + f"""
            Analyze round amount transactions for structuring:
            {json.dumps(pattern_data[:10], indent=2, default=str)}
            
            Focus on: amounts under thresholds, repeated patterns.
            
            Return same JSON format as above.
            """
        
        elif pattern_type == 'high_activity_periods':
            prompt = base_context + f"""
            Analyze high activity periods:
            {json.dumps(pattern_data[:5], indent=2, default=str)}
            
            Focus on: unusual spikes, coordinated activity.
            
            Return same JSON format as above.
            """
        
        else:
            prompt = base_context + f"""
            Analyze {pattern_type} pattern:
            {json.dumps(pattern_data[:5], indent=2, default=str)}
            
            Return same JSON format as above.
            """
        
        return prompt
    
    def _create_fallback_analysis(self, pattern_type: str, pattern_data: List[Dict]) -> Dict[str, Any]:
        """Create enhanced fallback analysis when LLM fails."""
        threads = []
        
        if pattern_type == 'frequent_pairs' and len(pattern_data) > 0:
            for i, pair in enumerate(pattern_data[:5]):  # Analyze more pairs
                transaction_count = pair.get('transaction_count', 0)
                total_amount = pair.get('total_amount', 0)
                avg_amount = pair.get('average_amount', 0)
                
                if transaction_count >= 5:
                    # Enhanced risk assessment
                    risk_level = 'high'
                    evidence = []
                    potential_violation = 'Potential layering or structuring'
                    
                    if transaction_count >= 10:
                        risk_level = 'high'
                        evidence.append(f"Very high frequency: {transaction_count} transactions")
                        potential_violation = 'High-frequency layering scheme'
                    elif transaction_count >= 8:
                        risk_level = 'high'
                        evidence.append(f"High frequency: {transaction_count} transactions")
                        potential_violation = 'Potential layering scheme'
                    else:
                        risk_level = 'medium'
                        evidence.append(f"Moderate frequency: {transaction_count} transactions")
                        potential_violation = 'Potential structuring'
                    
                    # Add amount-based evidence
                    if total_amount > 50000:
                        evidence.append(f"High total volume: ${total_amount:,.2f}")
                    elif total_amount > 10000:
                        evidence.append(f"Moderate total volume: ${total_amount:,.2f}")
                    
                    # Check for round amounts
                    if avg_amount % 1000 == 0:
                        evidence.append(f"Round average amount: ${avg_amount:,.2f}")
                        potential_violation += ' with round amounts'
                    
                    threads.append({
                        'thread_id': f'fallback_freq_{i}',
                        'description': f"High frequency transactions between {pair.get('sender_name', 'Unknown')} and {pair.get('receiver_name', 'Unknown')} ({transaction_count} transactions, ${total_amount:,.2f} total)",
                        'participants': [pair.get('sender_name', 'Unknown'), pair.get('receiver_name', 'Unknown')],
                        'risk_level': risk_level,
                        'evidence': evidence,
                        'transactions_involved': [str(t.get('transaction_id', '')) for t in pair.get('sample_transactions', [])],
                        'potential_violation': potential_violation,
                        'confidence_score': 0.7,
                        'recommended_action': 'Review transaction history and consider enhanced monitoring'
                    })
        
        elif pattern_type == 'round_amounts' and len(pattern_data) > 3:
            # Enhanced round amount analysis
            round_amounts = [t.get('amount', 0) for t in pattern_data]
            users = list(set([t.get('user_name', 'Unknown') for t in pattern_data]))
            
            # Check for structuring patterns
            under_10k = [amt for amt in round_amounts if 9000 <= amt <= 9999]
            under_5k = [amt for amt in round_amounts if 4000 <= amt <= 4999]
            
            risk_level = 'medium'
            evidence = [f"{len(pattern_data)} round amount transactions"]
            potential_violation = 'Potential structuring'
            
            if len(under_10k) > 0:
                evidence.append(f"{len(under_10k)} transactions just under $10,000 threshold")
                risk_level = 'high'
                potential_violation = 'Structuring to avoid reporting requirements'
            
            if len(under_5k) > 0:
                evidence.append(f"{len(under_5k)} transactions just under $5,000 threshold")
                if risk_level != 'high':
                    risk_level = 'medium'
            
            if len(users) > 5:
                evidence.append(f"Multiple users ({len(users)}) involved in round amount transactions")
            
            threads.append({
                'thread_id': 'fallback_round_1',
                'description': f"Round amount transactions detected ({len(pattern_data)} transactions across {len(users)} users)",
                'participants': users[:10],  # Limit to first 10 users
                'risk_level': risk_level,
                'evidence': evidence,
                'transactions_involved': [str(t.get('transaction_id', '')) for t in pattern_data[:10]],
                'potential_violation': potential_violation,
                'confidence_score': 0.8,
                'recommended_action': 'Review for potential structuring patterns and consider enhanced monitoring'
            })
        
        elif pattern_type == 'high_activity_periods' and len(pattern_data) > 0:
            for i, period in enumerate(pattern_data[:3]):
                transaction_count = period.get('transaction_count', 0)
                total_amount = period.get('total_amount', 0)
                unique_users = period.get('unique_users', 0)
                
                if transaction_count > 10:
                    risk_level = 'high' if transaction_count > 20 else 'medium'
                    evidence = [
                        f"{transaction_count} transactions in one hour",
                        f"Total amount: ${total_amount:,.2f}",
                        f"Unique users: {unique_users}"
                    ]
                    
                    if total_amount > 100000:
                        evidence.append("High-value transaction concentration")
                        risk_level = 'high'
                    
                    threads.append({
                        'thread_id': f'fallback_activity_{i}',
                        'description': f"Unusual activity spike: {transaction_count} transactions in one hour (${total_amount:,.2f} total)",
                        'participants': [],
                        'risk_level': risk_level,
                        'evidence': evidence,
                        'transactions_involved': [str(t.get('transaction_id', '')) for t in period.get('sample_transactions', [])],
                        'potential_violation': 'Coordinated suspicious activity',
                        'confidence_score': 0.6,
                        'recommended_action': 'Investigate coordinated activity and timing patterns'
                    })
        
        return {
            'threads': threads,
            'risk_level': 'high' if any(t['risk_level'] == 'high' for t in threads) else 'medium' if threads else 'low',
            'summary': f"Enhanced fallback analysis for {pattern_type}: {len(threads)} suspicious patterns identified with detailed risk assessment",
            'key_insights': [
                f"Analyzed {len(pattern_data)} data points",
                f"Identified {len(threads)} suspicious patterns",
                "Used enhanced risk assessment criteria"
            ]
        }
    
    def _parse_llm_response(self, response_text: str, pattern_type: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured information."""
        
        try:
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                structured_data = json.loads(json_text)
                
                # Ensure required fields exist
                if 'threads' not in structured_data:
                    structured_data['threads'] = []
                if 'risk_level' not in structured_data:
                    structured_data['risk_level'] = 'medium'
                if 'summary' not in structured_data:
                    structured_data['summary'] = 'Analysis completed'
                
                return structured_data
            
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from LLM response for {pattern_type}")
        
        # Fallback: create structured response from text
        return {
            'threads': self._extract_threads_from_text(response_text),
            'risk_level': self._extract_risk_level_from_text(response_text),
            'summary': response_text[:200] + '...' if len(response_text) > 200 else response_text
        }
    
    def _extract_threads_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract thread information from unstructured text."""
        # Simple extraction logic - can be enhanced
        threads = []
        
        # Look for suspicious indicators in text
        suspicious_keywords = ['suspicious', 'unusual', 'potential', 'risk', 'anomaly', 'pattern']
        
        if any(keyword in text.lower() for keyword in suspicious_keywords):
            threads.append({
                'thread_id': f'thread_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'description': 'Potential suspicious activity identified',
                'participants': [],
                'risk_level': 'medium',
                'evidence': [text[:100] + '...'],
                'transactions_involved': [],
                'potential_violation': 'Unknown'
            })
        
        return threads
    
    def _extract_risk_level_from_text(self, text: str) -> str:
        """Extract risk level from text."""
        text_lower = text.lower()
        
        if 'high risk' in text_lower or 'highly suspicious' in text_lower:
            return 'high'
        elif 'low risk' in text_lower or 'minimal risk' in text_lower:
            return 'low'
        else:
            return 'medium'
    
    def _generate_overall_analysis(self, analysis_results: Dict[str, Any], summary_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall analysis across all patterns."""
        
        # Collect all threads
        all_threads = []
        risk_levels = []
        
        for pattern_type, analysis in analysis_results.items():
            if isinstance(analysis, dict) and 'threads' in analysis:
                all_threads.extend(analysis['threads'])
                risk_levels.append(analysis.get('risk_level', 'medium'))
        
        # Determine overall risk
        high_risk_count = risk_levels.count('high')
        medium_risk_count = risk_levels.count('medium')
        
        if high_risk_count >= 2:
            overall_risk = 'high'
        elif high_risk_count >= 1 or medium_risk_count >= 3:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        # Create summary prompt for overall analysis
        summary_prompt = f"""
        Based on the analysis of transaction patterns, provide an executive summary:
        
        - Total suspicious threads identified: {len(all_threads)}
        - Pattern types analyzed: {len(analysis_results)}
        - Overall risk assessment: {overall_risk}
        
        Key findings:
        {json.dumps([thread['description'] for thread in all_threads[:5]], indent=2)}
        
        Provide a brief executive summary (2-3 sentences) and key recommendations.
        """
        
        try:
            response = self.model.generate_content(summary_prompt)
            executive_summary = response.text
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            executive_summary = f"Analysis completed. {len(all_threads)} suspicious threads identified across {len(analysis_results)} pattern types."
        
        return {
            'total_threads': len(all_threads),
            'overall_risk_level': overall_risk,
            'executive_summary': executive_summary,
            'pattern_summary': {
                pattern_type: {
                    'thread_count': len(analysis.get('threads', [])),
                    'risk_level': analysis.get('risk_level', 'unknown')
                }
                for pattern_type, analysis in analysis_results.items()
                if isinstance(analysis, dict)
            },
            'top_threats': sorted(all_threads, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x.get('risk_level', 'low'), 1), reverse=True)[:5]
        }
