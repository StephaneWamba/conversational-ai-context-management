-- Create constraints table for storing user preferences, rules, and corrections
CREATE TABLE IF NOT EXISTS conversation_constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    constraint_type VARCHAR(50) NOT NULL, -- 'preference', 'rule', 'correction', 'fact', 'ban'
    constraint_key VARCHAR(255) NOT NULL, -- e.g., 'answer_style', 'age', 'metrics_definition'
    constraint_value JSONB NOT NULL, -- The actual constraint value
    turn_number INTEGER NOT NULL, -- Turn when constraint was established
    superseded_by UUID REFERENCES conversation_constraints(id), -- For corrections
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_constraints_conversation_id ON conversation_constraints(conversation_id);
CREATE INDEX IF NOT EXISTS idx_constraints_active ON conversation_constraints(conversation_id, is_active);
CREATE INDEX IF NOT EXISTS idx_constraints_type ON conversation_constraints(conversation_id, constraint_type);
CREATE INDEX IF NOT EXISTS idx_constraints_key ON conversation_constraints(conversation_id, constraint_key);

