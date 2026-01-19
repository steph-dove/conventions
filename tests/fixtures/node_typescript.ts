/**
 * Example TypeScript file demonstrating conventions.
 */
import { Request, Response, NextFunction } from 'express';

interface User {
    id: number;
    name: string;
    email: string;
    createdAt: Date;
}

interface Config {
    apiUrl: string;
    timeout: number;
    retries: number;
}

/**
 * User service for managing user operations.
 */
export class UserService {
    private config: Config;
    private cache: Map<number, User>;

    /**
     * Create a new UserService instance.
     * @param config - Service configuration
     */
    constructor(config: Config) {
        this.config = config;
        this.cache = new Map();
    }

    /**
     * Find a user by their ID.
     * @param id - The user's ID
     * @returns The user or null if not found
     */
    async findById(id: number): Promise<User | null> {
        // Check cache first
        if (this.cache.has(id)) {
            return this.cache.get(id)!;
        }

        try {
            const response = await fetch(`${this.config.apiUrl}/users/${id}`);
            if (!response.ok) {
                return null;
            }
            const user = await response.json() as User;
            this.cache.set(id, user);
            return user;
        } catch (error) {
            console.error('Failed to fetch user:', error);
            return null;
        }
    }

    /**
     * Create a new user.
     * @param userData - User data to create
     * @returns The created user
     */
    async create(userData: Omit<User, 'id' | 'createdAt'>): Promise<User> {
        const response = await fetch(`${this.config.apiUrl}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData),
        });

        if (!response.ok) {
            throw new Error(`Failed to create user: ${response.statusText}`);
        }

        return response.json();
    }
}

/**
 * Error handler middleware.
 * @param err - Error object
 * @param req - Express request
 * @param res - Express response
 * @param next - Next function
 */
export function errorHandler(
    err: Error,
    req: Request,
    res: Response,
    next: NextFunction
): void {
    console.error('Error:', err.message);
    res.status(500).json({ error: err.message });
}

/**
 * Request logger middleware.
 * @param req - Express request
 * @param res - Express response
 * @param next - Next function
 */
export function requestLogger(
    req: Request,
    res: Response,
    next: NextFunction
): void {
    console.log(`${req.method} ${req.path}`);
    next();
}

/**
 * Validate user input.
 * @param data - Data to validate
 * @returns Validation result
 */
export function validateUser(data: unknown): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!data || typeof data !== 'object') {
        return { valid: false, errors: ['Invalid data format'] };
    }

    const user = data as Partial<User>;

    if (!user.name || user.name.trim().length === 0) {
        errors.push('Name is required');
    }

    if (!user.email || !user.email.includes('@')) {
        errors.push('Valid email is required');
    }

    return { valid: errors.length === 0, errors };
}
