"""
Real Web Search Tools - Updated for duckduckgo-search v8.1.1 (2025)
HASHIRU 6.1 - Internet access with real search capabilities
"""
import asyncio
import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Import DuckDuckGo search (latest version)
try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
    print("✅ DuckDuckGo search library v8.1.1+ loaded")
except ImportError:
    DDG_AVAILABLE = False
    print("⚠️ DuckDuckGo search not available. Install: pip install duckduckgo-search")


async def handle_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Real internet search using DuckDuckGo (v8.1.1+ API)
    Usage: /search <query> [max_results]
    """
    if not query.strip():
        return {"error": "Search query cannot be empty"}
    
    if not DDG_AVAILABLE:
        return {"error": "DuckDuckGo search library not installed. Run: pip install duckduckgo-search"}
    
    try:
        # Use context manager for DDGS (recommended in v8+)
        with DDGS() as ddgs:
            # Perform search - new API doesn't use max_results in function call
            search_results = ddgs.text(
                keywords=query,
                region="us-en",
                safesearch="moderate"
            )
            
            # Limit results manually (new API behavior)
            results = []
            for i, result in enumerate(search_results):
                if i >= max_results:
                    break
                    
                results.append({
                    "position": i + 1,
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "domain": result.get("href", "").split('/')[2] if result.get("href") else ""
                })
        
        # Save search results to free path
        search_data = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "total_results": len(results),
            "results": results,
            "api_version": "duckduckgo-search v8.1.1+"
        }
        
        # Save to free project folder
        free_path = Path(r"C:\meu_projeto_livre")
        free_path.mkdir(exist_ok=True)
        search_file = free_path / f"search_{query.replace(' ', '_')[:20]}_{int(datetime.now().timestamp())}.json"
        
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_engine": "DuckDuckGo v8.1.1+",
            "saved_to": str(search_file),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


async def handle_news(topic: str = "technology", max_results: int = 5) -> Dict[str, Any]:
    """
    Search for news using updated API
    Usage: /news [topic] [max_results]
    """
    if not DDG_AVAILABLE:
        return {"error": "DuckDuckGo search library not installed"}
    
    try:
        with DDGS() as ddgs:
            # News search with new API
            news_results = ddgs.news(
                keywords=topic,
                region="us-en",
                safesearch="moderate"
            )
            
            articles = []
            for i, article in enumerate(news_results):
                if i >= max_results:
                    break
                    
                articles.append({
                    "position": i + 1,
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", ""),
                    "published": article.get("date", ""),
                    "snippet": article.get("body", "")
                })
        
        # Save news to free path
        news_data = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "articles": articles,
            "total_articles": len(articles),
            "api_version": "duckduckgo-search v8.1.1+"
        }
        
        free_path = Path(r"C:\meu_projeto_livre")
        news_file = free_path / f"news_{topic.replace(' ', '_')[:15]}_{int(datetime.now().timestamp())}.json"
        
        with open(news_file, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "topic": topic,
            "articles": articles,
            "total_found": len(articles),
            "saved_to": str(news_file),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"News search failed: {str(e)}"}


async def handle_images(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for images using updated API
    Usage: /images <query> [max_results]
    """
    if not query.strip():
        return {"error": "Image search query cannot be empty"}
        
    if not DDG_AVAILABLE:
        return {"error": "DuckDuckGo search library not installed"}
    
    try:
        with DDGS() as ddgs:
            # Image search with new API
            image_results = ddgs.images(
                keywords=query,
                region="us-en",
                safesearch="moderate"
            )
            
            images = []
            for i, img in enumerate(image_results):
                if i >= max_results:
                    break
                    
                images.append({
                    "position": i + 1,
                    "title": img.get("title", ""),
                    "image_url": img.get("image", ""),
                    "thumbnail": img.get("thumbnail", ""),
                    "source_url": img.get("url", ""),
                    "width": img.get("width", 0),
                    "height": img.get("height", 0)
                })
        
        return {
            "success": True,
            "query": query,
            "images": images,
            "total_found": len(images),
            "search_engine": "DuckDuckGo Images v8.1.1+",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Image search failed: {str(e)}"}


async def handle_videos(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for videos using updated API
    Usage: /videos <query> [max_results]
    """
    if not query.strip():
        return {"error": "Video search query cannot be empty"}
        
    if not DDG_AVAILABLE:
        return {"error": "DuckDuckGo search library not installed"}
    
    try:
        with DDGS() as ddgs:
            # Video search with new API
            video_results = ddgs.videos(
                keywords=query,
                region="us-en",
                safesearch="moderate"
            )
            
            videos = []
            for i, video in enumerate(video_results):
                if i >= max_results:
                    break
                    
                videos.append({
                    "position": i + 1,
                    "title": video.get("title", ""),
                    "video_url": video.get("content", ""),
                    "thumbnail": video.get("image", ""),
                    "duration": video.get("duration", ""),
                    "published": video.get("published", ""),
                    "publisher": video.get("publisher", "")
                })
        
        return {
            "success": True,
            "query": query,
            "videos": videos,
            "total_found": len(videos),
            "search_engine": "DuckDuckGo Videos v8.1.1+",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Video search failed: {str(e)}"}


async def handle_instant_answer(query: str) -> Dict[str, Any]:
    """
    Get instant answers/facts from DuckDuckGo
    Usage: /instant <query>
    """
    if not query.strip():
        return {"error": "Query cannot be empty"}
        
    if not DDG_AVAILABLE:
        return {"error": "DuckDuckGo search library not installed"}
    
    try:
        with DDGS() as ddgs:
            # Try to get instant answer
            answer_results = ddgs.answers(query)
            
            answers = []
            for answer in answer_results:
                answers.append({
                    "text": answer.get("text", ""),
                    "url": answer.get("url", ""),
                    "source": answer.get("source", "")
                })
                break  # Usually just one answer
        
        if not answers:
            return {"error": "No instant answer found", "query": query}
        
        return {
            "success": True,
            "query": query,
            "instant_answer": answers[0],
            "search_engine": "DuckDuckGo Instant Answers",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Instant answer failed: {str(e)}"}


async def handle_browse(url: str) -> Dict[str, Any]:
    """
    Fetch content from a specific URL
    Usage: /browse <URL>
    """
    if not url.strip():
        return {"error": "URL cannot be empty"}
    
    # Add https:// if no protocol
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    try:
        headers = {
            "User-Agent": "HASHIRU-6.1-Agent",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content = response.text
            content_preview = content[:2000] + "..." if len(content) > 2000 else content
            
            # Save content to free path
            free_path = Path(r"C:\meu_projeto_livre")
            domain = url.split('/')[2] if '/' in url else url.replace(':', '_')
            content_file = free_path / f"browsed_{domain}_{int(datetime.now().timestamp())}.html"
            
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "content_length": len(content),
                "content_preview": content_preview,
                "saved_to": str(content_file),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {"error": f"Failed to browse URL: {str(e)}"}


async def handle_research(topic: str, depth: str = "basic") -> Dict[str, Any]:
    """
    Comprehensive research using multiple search types
    Usage: /research <topic> [basic|detailed]
    """
    if not topic.strip():
        return {"error": "Research topic cannot be empty"}
    
    if not DDG_AVAILABLE:
        return {"error": "DuckDuckGo search library not installed"}
    
    try:
        research_data = {
            "topic": topic,
            "depth": depth,
            "timestamp": datetime.now().isoformat(),
            "web_results": [],
            "news_results": [],
            "instant_answers": [],
            "api_version": "duckduckgo-search v8.1.1+"
        }
        
        with DDGS() as ddgs:
            # 1. Web search
            web_results = ddgs.text(keywords=topic, region="us-en", safesearch="moderate")
            for i, result in enumerate(web_results):
                if i >= 5:  # Limit for research
                    break
                research_data["web_results"].append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            
            # 2. News search  
            try:
                news_results = ddgs.news(keywords=topic, region="us-en", safesearch="moderate")
                for i, news in enumerate(news_results):
                    if i >= 3:  # Limit for research
                        break
                    research_data["news_results"].append({
                        "title": news.get("title", ""),
                        "url": news.get("url", ""),
                        "source": news.get("source", ""),
                        "date": news.get("date", "")
                    })
            except:
                pass  # News might not be available for all topics
            
            # 3. Try instant answers
            try:
                answers = ddgs.answers(topic)
                for answer in answers:
                    research_data["instant_answers"].append({
                        "text": answer.get("text", ""),
                        "url": answer.get("url", ""),
                        "source": answer.get("source", "")
                    })
                    break  # Usually just one answer
            except:
                pass  # Instant answers might not be available
        
        # Save comprehensive research
        free_path = Path(r"C:\meu_projeto_livre")
        research_file = free_path / f"research_{topic.replace(' ', '_')[:20]}_{int(datetime.now().timestamp())}.json"
        
        with open(research_file, 'w', encoding='utf-8') as f:
            json.dump(research_data, f, indent=2, ensure_ascii=False)
        
        # Generate summary
        total_sources = len(research_data["web_results"]) + len(research_data["news_results"])
        has_instant = len(research_data["instant_answers"]) > 0
        
        return {
            "success": True,
            "topic": topic,
            "depth": depth,
            "total_sources": total_sources,
            "has_instant_answer": has_instant,
            "saved_to": str(research_file),
            "summary": f"Research complete: {total_sources} sources found for '{topic}'",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Research failed: {str(e)}"}


# Updated command registry
WEB_COMMANDS = {
    "/search": handle_search,
    "/news": handle_news,
    "/images": handle_images,
    "/videos": handle_videos,
    "/instant": handle_instant_answer,
    "/browse": handle_browse,
    "/research": handle_research,
}

# Register commands function
def register_web_commands():
    """Register web commands in the main system"""
    try:
        from tools.registry import register_handler
        
        for command, handler in WEB_COMMANDS.items():
            register_handler(command, handler)
            
        print("✅ Real web search commands registered (v8.1.1+):")
        for cmd in WEB_COMMANDS.keys():
            print(f"   {cmd}")
            
        if DDG_AVAILABLE:
            print("🌐 DuckDuckGo search engine ready (latest API)!")
        else:
            print("⚠️  Install duckduckgo-search for full functionality")
            
    except Exception as e:
        print(f"⚠️ Error registering web commands: {e}")

# Auto-register on import
register_web_commands()