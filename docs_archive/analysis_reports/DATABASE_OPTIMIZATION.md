# Database Optimization and Indexes

## Current Index Analysis

### Models Requiring Indexes

Based on common query patterns in the codebase:

#### 1. TimeEntry Model
- **ForeignKey indexes**: Already have default indexes
- **Date filtering**: `date` field frequently filtered
- **Status queries**: `status` field used in filters
- **Recommendation**: Add composite index on `(project, date)` for common queries

#### 2. Task Model
- **Status filtering**: `status` field heavily filtered
- **Date queries**: `due_date`, `created_at` used in ordering
- **Priority sorting**: `priority` used in queries
- **Recommendation**: Add composite index on `(project, status, due_date)`

#### 3. Expense/Income Models
- **Date range queries**: `date` field used for reporting
- **Project filtering**: Combined with date for analytics
- **Recommendation**: Add composite index on `(project, date)`

#### 4. Schedule Model
- **Date range queries**: `start`, `end` fields for calendar views
- **User filtering**: Combined with dates
- **Recommendation**: Add composite index on `(user, start, end)`

#### 5. Message Model (Chat)
- **Channel queries**: `channel` + `created_at` for message history
- **Unread messages**: `is_read` + `recipient` for notifications
- **Recommendation**: Add composite index on `(channel, created_at)` and `(recipient, is_read)`

## Implementation

Create migration with these indexes:

```python
# In a new migration file
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', 'XXXX_previous_migration'),
    ]

    operations = [
        # TimeEntry indexes
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['project', 'date'], name='timeentry_proj_date_idx'),
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['date', '-id'], name='timeentry_date_desc_idx'),
        ),
        
        # Task indexes
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'status', 'due_date'], name='task_proj_stat_due_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['status', '-priority'], name='task_stat_priority_idx'),
        ),
        
        # Expense indexes
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['project', 'date'], name='expense_proj_date_idx'),
        ),
        
        # Income indexes
        migrations.AddIndex(
            model_name='income',
            index=models.Index(fields=['project', 'date'], name='income_proj_date_idx'),
        ),
        
        # Schedule indexes
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['user', 'start', 'end'], name='schedule_user_dates_idx'),
        ),
        
        # Message indexes (if exists)
        # migrations.AddIndex(
        #     model_name='message',
        #     index=models.Index(fields=['channel', '-created_at'], name='message_chan_created_idx'),
        # ),
        # migrations.AddIndex(
        #     model_name='message',
        #     index=models.Index(fields=['recipient', 'is_read'], name='message_recip_read_idx'),
        # ),
    ]
```

## Query Optimization Recommendations

1. **Use select_related() for ForeignKey**: Reduces N+1 queries
   ```python
   TimeEntry.objects.select_related('project', 'user').all()
   ```

2. **Use prefetch_related() for Many-to-Many**: Reduces queries for related sets
   ```python
   Project.objects.prefetch_related('tasks', 'expenses').all()
   ```

3. **Use only() for specific fields**: Reduces data transfer
   ```python
   Task.objects.only('id', 'title', 'status')
   ```

4. **Use defer() to exclude large fields**: Skip TextField, JSONField if not needed
   ```python
   Project.objects.defer('description', 'notes')
   ```

5. **Pagination**: Always paginate large result sets
   ```python
   from django.core.paginator import Paginator
   paginator = Paginator(queryset, 25)
   ```

## Database Statistics

Run these queries in production to analyze performance:

```sql
-- Find missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY abs(correlation) DESC;

-- Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Monitoring

- Use Django Debug Toolbar in development to identify slow queries
- Enable PostgreSQL slow query log in production (log queries > 100ms)
- Monitor index usage with pg_stat_user_indexes
- Run VACUUM ANALYZE regularly (automatic on managed services)

## Implementation Schedule

1. **Phase 1**: Add indexes for most frequently queried models (TimeEntry, Task)
2. **Phase 2**: Add indexes for reporting queries (Expense, Income)
3. **Phase 3**: Add indexes for real-time features (Message, Schedule)
4. **Phase 4**: Analyze production query logs and add additional indexes as needed
