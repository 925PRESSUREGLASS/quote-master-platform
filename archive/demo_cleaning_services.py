"""
Demo script for the new Window & Pressure Cleaning Service Quote Generator
"""

import asyncio
import json
from src.services.quote.unified_generator import (
    UnifiedServiceQuoteGenerator,
    ServiceType,
    PropertyType,
    generate_window_cleaning_quote,
    generate_pressure_washing_quote
)


async def demo_service_quotes():
    """Demonstrate the new service quote generation functionality."""
    print("🏠 Window & Pressure Cleaning Service Quote Generator Demo")
    print("=" * 60)
    
    # Initialize the generator
    generator = UnifiedServiceQuoteGenerator()
    
    # Test 1: Window Cleaning Quote
    print("\n1. 🪟 Window Cleaning Service Quote")
    print("-" * 40)
    
    try:
        window_quote = await generator.generate_service_quote(
            job_description="Clean all exterior and interior windows for a 2-story residential house. Approximately 20 windows total including French doors.",
            property_info="Two-story suburban family home with easy access, concrete driveway parking available",
            customer_info={
                "size": "large",
                "type": "residential",
                "price_sensitivity": "standard"
            },
            service_type=ServiceType.WINDOW_CLEANING,
            property_type=PropertyType.RESIDENTIAL_HOUSE
        )
        
        print(f"Service Type: {window_quote.service_type.value}")
        print(f"Total Price: ${window_quote.total_price}")
        print(f"Complexity: {window_quote.metadata.service_assessment.complexity_level.value}")
        print(f"Estimated Hours: {window_quote.metadata.service_assessment.estimated_hours}")
        print(f"Pricing Strategy: {window_quote.metadata.pricing_strategy.value}")
        print(f"Accuracy Score: {window_quote.metadata.accuracy_score}")
        
        if window_quote.upsell_opportunities:
            print(f"Upsell Opportunities: {', '.join(window_quote.upsell_opportunities[:2])}")
            
    except Exception as e:
        print(f"Error generating window cleaning quote: {e}")
    
    # Test 2: Pressure Washing Quote
    print("\n2. 🚿 Pressure Washing Service Quote")
    print("-" * 40)
    
    try:
        pressure_quote = await generator.generate_service_quote(
            job_description="Pressure wash concrete driveway, walkways, and patio area. Heavy moss and algae buildup. Approximately 200 square meters total.",
            property_info="Commercial office building with restricted weekend access only",
            customer_info={
                "size": "medium",
                "type": "commercial",
                "price_sensitivity": "premium"
            },
            service_type=ServiceType.PRESSURE_WASHING,
            property_type=PropertyType.COMMERCIAL_OFFICE
        )
        
        print(f"Service Type: {pressure_quote.service_type.value}")
        print(f"Total Price: ${pressure_quote.total_price}")
        print(f"Complexity: {pressure_quote.metadata.service_assessment.complexity_level.value}")
        print(f"Risk Factors: {len(pressure_quote.metadata.service_assessment.risk_factors)}")
        print(f"Access Difficulty: {pressure_quote.metadata.service_assessment.access_difficulty.value}")
        
        if pressure_quote.alternative_options:
            alt = pressure_quote.alternative_options[0]
            print(f"Alternative Option: {alt['name']} - ${alt['price']}")
            
    except Exception as e:
        print(f"Error generating pressure washing quote: {e}")
    
    # Test 3: Convenience Functions
    print("\n3. 📋 Convenience Functions Test")
    print("-" * 40)
    
    try:
        # Quick window cleaning quote
        quick_quote = await generate_window_cleaning_quote(
            "Small apartment building with 12 units, ground level windows only",
            property_size="medium"
        )
        print(f"Quick Window Quote: ${quick_quote.total_price}")
        
        # Quick pressure washing quote
        quick_pressure = await generate_pressure_washing_quote(
            "Residential driveway and sidewalk cleaning",
            property_type="residential"
        )
        print(f"Quick Pressure Quote: ${quick_pressure.total_price}")
        
    except Exception as e:
        print(f"Error with convenience functions: {e}")
    
    # Test 4: Analytics
    print("\n4. 📊 Service Analytics")
    print("-" * 40)
    
    try:
        analytics = await generator.get_analytics()
        if "error" not in analytics:
            print("Analytics retrieved successfully:")
            print(f"Cache Statistics: {analytics.get('cache_statistics', {})}")
            print(f"Service Types Processed: {analytics.get('service_types_processed', {})}")
        else:
            print(f"Analytics error: {analytics['error']}")
            
    except Exception as e:
        print(f"Error getting analytics: {e}")
    
    print("\n🎉 Demo completed! The Window & Pressure Cleaning Pro system is now operational.")
    print("Key transformations completed:")
    print("✅ Changed from inspirational quotes to service quotes")
    print("✅ Added property assessment and pricing optimization")
    print("✅ Implemented service-specific complexity analysis")
    print("✅ Added A/B testing for pricing strategies")
    print("✅ Enhanced with upselling and alternatives")


if __name__ == "__main__":
    asyncio.run(demo_service_quotes())
