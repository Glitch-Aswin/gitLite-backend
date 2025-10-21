# SQL Commands to Fix User Table RLS Policies

Run these commands in your Supabase SQL Editor:

## 1. Check if users table exists and has proper structure
```sql
-- Check table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

## 2. Enable RLS (if not already enabled)
```sql
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
```

## 3. Create RLS Policies

### Policy 1: Users can read their own profile
```sql
CREATE POLICY "Users can view their own profile"
ON public.users
FOR SELECT
USING (auth.uid() = id);
```

### Policy 2: Users can insert their own profile (for auto-creation on login)
```sql
CREATE POLICY "Users can insert their own profile"
ON public.users
FOR INSERT
WITH CHECK (auth.uid() = id);
```

### Policy 3: Users can update their own profile
```sql
CREATE POLICY "Users can update their own profile"
ON public.users
FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);
```

### Policy 4: Anyone can view public profile data (optional - for user lookup)
```sql
CREATE POLICY "Anyone can view public profiles"
ON public.users
FOR SELECT
USING (true);
```

## 4. Grant proper permissions
```sql
GRANT SELECT, INSERT, UPDATE ON public.users TO authenticated;
GRANT SELECT ON public.users TO anon;
```

## 5. Verify policies
```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'users';
```

---

## If users table doesn't exist, create it:
```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    bio TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own profile"
ON public.users FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
ON public.users FOR INSERT
WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
ON public.users FOR UPDATE
USING (auth.uid() = id);

CREATE POLICY "Anyone can view public profiles"
ON public.users FOR SELECT
USING (true);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON public.users TO authenticated;
GRANT SELECT ON public.users TO anon;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```
