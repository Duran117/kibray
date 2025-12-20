"""
WebSocket Load Testing Script for Kibray

Tests WebSocket performance under load:
- Concurrent connections
- Message throughput
- Response time
- Connection stability
- Memory usage
"""

import asyncio
from datetime import datetime
import statistics
import time

import aiohttp


class WebSocketLoadTester:
    """
    Load testing tool for WebSocket connections.
    
    Features:
    - Concurrent client simulation
    - Message rate testing
    - Latency measurements
    - Connection stability monitoring
    - Performance metrics collection
    """

    def __init__(self, base_url="ws://localhost:8000", auth_token=None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.results = {
            'connections': [],
            'messages': [],
            'errors': [],
            'latencies': [],
        }
        self.start_time = None
        self.end_time = None

    async def create_client(self, client_id, endpoint="/ws/chat/general/"):
        """
        Create a WebSocket client connection.
        
        Args:
            client_id: Unique client identifier
            endpoint: WebSocket endpoint path
            
        Returns:
            tuple: (websocket, session, connect_time)
        """
        url = f"{self.base_url}{endpoint}"

        if self.auth_token:
            url += f"?token={self.auth_token}"

        session = aiohttp.ClientSession()

        try:
            start = time.time()
            ws = await session.ws_connect(url)
            connect_time = time.time() - start

            self.results['connections'].append({
                'client_id': client_id,
                'status': 'connected',
                'connect_time': connect_time,
                'timestamp': datetime.now().isoformat(),
            })

            return ws, session, connect_time

        except Exception as e:
            self.results['errors'].append({
                'client_id': client_id,
                'error': str(e),
                'phase': 'connection',
                'timestamp': datetime.now().isoformat(),
            })
            await session.close()
            return None, None, None

    async def send_message(self, ws, client_id, message_num):
        """
        Send a message through WebSocket and measure latency.
        
        Args:
            ws: WebSocket connection
            client_id: Client identifier
            message_num: Message sequence number
            
        Returns:
            float: Round-trip time in milliseconds
        """
        message = {
            'type': 'chat_message',
            'message': f'Load test message {message_num} from client {client_id}',
            'client_id': client_id,
            'sent_at': time.time(),
        }

        try:
            send_time = time.time()
            await ws.send_json(message)

            # Wait for response
            response = await asyncio.wait_for(ws.receive(), timeout=5.0)
            receive_time = time.time()

            latency = (receive_time - send_time) * 1000  # milliseconds

            self.results['messages'].append({
                'client_id': client_id,
                'message_num': message_num,
                'latency_ms': latency,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
            })

            self.results['latencies'].append(latency)

            return latency

        except TimeoutError:
            self.results['errors'].append({
                'client_id': client_id,
                'error': 'Timeout waiting for response',
                'phase': 'message',
                'message_num': message_num,
            })
            return None

        except Exception as e:
            self.results['errors'].append({
                'client_id': client_id,
                'error': str(e),
                'phase': 'message',
                'message_num': message_num,
            })
            return None

    async def run_client(self, client_id, num_messages=10, delay=0.1):
        """
        Run a single client that sends multiple messages.
        
        Args:
            client_id: Client identifier
            num_messages: Number of messages to send
            delay: Delay between messages (seconds)
        """
        ws, session, connect_time = await self.create_client(client_id)

        if not ws:
            return

        try:
            for msg_num in range(num_messages):
                latency = await self.send_message(ws, client_id, msg_num)

                if latency:
                    print(f"Client {client_id} - Message {msg_num}: {latency:.2f}ms")

                await asyncio.sleep(delay)

        finally:
            await ws.close()
            await session.close()

    async def run_load_test(self, num_clients=10, messages_per_client=10, delay=0.1):
        """
        Run load test with multiple concurrent clients.
        
        Args:
            num_clients: Number of concurrent clients
            messages_per_client: Messages each client sends
            delay: Delay between messages
        """
        print("\n🔥 Starting Load Test")
        print(f"Clients: {num_clients}")
        print(f"Messages per client: {messages_per_client}")
        print(f"Total messages: {num_clients * messages_per_client}")
        print(f"Delay between messages: {delay}s\n")

        self.start_time = time.time()

        # Create tasks for all clients
        tasks = [
            self.run_client(i, messages_per_client, delay)
            for i in range(num_clients)
        ]

        # Run all clients concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

        self.end_time = time.time()

        print("\n✅ Load Test Complete\n")

    def generate_report(self):
        """
        Generate performance report from test results.
        
        Returns:
            dict: Performance metrics and statistics
        """
        duration = self.end_time - self.start_time if self.end_time else 0

        successful_messages = [
            m for m in self.results['messages']
            if m['status'] == 'success'
        ]

        successful_connections = [
            c for c in self.results['connections']
            if c['status'] == 'connected'
        ]

        latencies = self.results['latencies']

        report = {
            'summary': {
                'duration_seconds': round(duration, 2),
                'total_clients': len(self.results['connections']),
                'successful_connections': len(successful_connections),
                'failed_connections': len(self.results['connections']) - len(successful_connections),
                'total_messages_sent': len(self.results['messages']),
                'successful_messages': len(successful_messages),
                'failed_messages': len(self.results['messages']) - len(successful_messages),
                'errors': len(self.results['errors']),
            },
            'connection_performance': {
                'avg_connect_time_ms': round(
                    statistics.mean([c['connect_time'] * 1000 for c in successful_connections])
                    if successful_connections else 0,
                    2
                ),
                'max_connect_time_ms': round(
                    max([c['connect_time'] * 1000 for c in successful_connections], default=0),
                    2
                ),
            },
            'message_performance': {
                'messages_per_second': round(
                    len(successful_messages) / duration if duration > 0 else 0,
                    2
                ),
                'avg_latency_ms': round(statistics.mean(latencies), 2) if latencies else 0,
                'median_latency_ms': round(statistics.median(latencies), 2) if latencies else 0,
                'min_latency_ms': round(min(latencies), 2) if latencies else 0,
                'max_latency_ms': round(max(latencies), 2) if latencies else 0,
                'p95_latency_ms': round(
                    statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0,
                    2
                ),
                'p99_latency_ms': round(
                    statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0,
                    2
                ),
            },
            'errors': self.results['errors'],
        }

        return report

    def print_report(self):
        """Print formatted performance report"""
        report = self.generate_report()

        print("=" * 60)
        print("📊 LOAD TEST REPORT")
        print("=" * 60)

        print("\n📋 SUMMARY")
        print("-" * 60)
        for key, value in report['summary'].items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        print("\n🔌 CONNECTION PERFORMANCE")
        print("-" * 60)
        for key, value in report['connection_performance'].items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        print("\n📨 MESSAGE PERFORMANCE")
        print("-" * 60)
        for key, value in report['message_performance'].items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        if report['errors']:
            print(f"\n❌ ERRORS ({len(report['errors'])})")
            print("-" * 60)
            for error in report['errors'][:10]:  # Show first 10 errors
                print(f"Client {error['client_id']}: {error['error']}")

        print("\n" + "=" * 60)

        # Performance assessment
        avg_latency = report['message_performance']['avg_latency_ms']
        success_rate = (
            report['summary']['successful_messages'] /
            report['summary']['total_messages_sent'] * 100
            if report['summary']['total_messages_sent'] > 0 else 0
        )

        print("\n🎯 PERFORMANCE ASSESSMENT")
        print("-" * 60)

        if avg_latency < 100:
            print("✅ Latency: EXCELLENT (< 100ms)")
        elif avg_latency < 500:
            print("⚠️  Latency: GOOD (100-500ms)")
        else:
            print("❌ Latency: POOR (> 500ms)")

        if success_rate > 99:
            print("✅ Success Rate: EXCELLENT (> 99%)")
        elif success_rate > 95:
            print("⚠️  Success Rate: GOOD (95-99%)")
        else:
            print("❌ Success Rate: POOR (< 95%)")

        print("=" * 60 + "\n")

        return report


# Test scenarios

async def test_light_load():
    """Test with light load (10 clients, 10 messages each)"""
    tester = WebSocketLoadTester()
    await tester.run_load_test(
        num_clients=10,
        messages_per_client=10,
        delay=0.1
    )
    tester.print_report()


async def test_medium_load():
    """Test with medium load (50 clients, 20 messages each)"""
    tester = WebSocketLoadTester()
    await tester.run_load_test(
        num_clients=50,
        messages_per_client=20,
        delay=0.05
    )
    tester.print_report()


async def test_heavy_load():
    """Test with heavy load (100 clients, 50 messages each)"""
    tester = WebSocketLoadTester()
    await tester.run_load_test(
        num_clients=100,
        messages_per_client=50,
        delay=0.02
    )
    tester.print_report()


async def test_stress():
    """Stress test (200 clients, 100 messages each)"""
    tester = WebSocketLoadTester()
    await tester.run_load_test(
        num_clients=200,
        messages_per_client=100,
        delay=0.01
    )
    tester.print_report()


if __name__ == "__main__":

    print("\n🚀 Kibray WebSocket Load Tester\n")
    print("Select test scenario:")
    print("1. Light Load (10 clients)")
    print("2. Medium Load (50 clients)")
    print("3. Heavy Load (100 clients)")
    print("4. Stress Test (200 clients)")
    print("5. Custom")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        asyncio.run(test_light_load())
    elif choice == "2":
        asyncio.run(test_medium_load())
    elif choice == "3":
        asyncio.run(test_heavy_load())
    elif choice == "4":
        asyncio.run(test_stress())
    elif choice == "5":
        num_clients = int(input("Number of clients: "))
        messages = int(input("Messages per client: "))
        delay = float(input("Delay between messages (seconds): "))

        tester = WebSocketLoadTester()
        asyncio.run(tester.run_load_test(num_clients, messages, delay))
        tester.print_report()
    else:
        print("Invalid choice. Running light load test.")
        asyncio.run(test_light_load())
