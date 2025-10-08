# Clean Architecture & Domain-Driven Design Guidelines

## Overview

This document outlines the architectural principles and development guidelines for the PurposePath C# backend migration, following Clean Architecture and Domain-Driven Design (DDD) principles.

## Architecture Layers

### 1. Domain Layer (Core)

**Purpose**: Contains business logic, entities, value objects, and domain services
**Dependencies**: None (Pure business logic)
**Location**: `PurposePath.Domain`

#### Principles

- No dependencies on other layers or external frameworks
- Contains business rules and domain logic only
- Uses pure C# types and .NET framework primitives only
- All business invariants are enforced here

#### Components

- **Entities**: Core business objects with identity (User, Tenant, Subscription)
- **Value Objects**: Immutable objects without identity (Email, UserId, Money)
- **Domain Services**: Business logic that doesn't naturally fit in entities
- **Repository Interfaces**: Contracts for data access (defined here, implemented elsewhere)
- **Domain Events**: Represent something important that happened in the domain

#### Guidelines

```csharp
// ✅ Good - Pure domain logic
public class User : BaseEntity
{
    public void Activate()
    {
        if (Status == UserStatus.Deleted)
            throw new DomainException("Cannot activate deleted user");
        
        Status = UserStatus.Active;
        AddDomainEvent(new UserActivatedEvent(Id));
    }
}

// ❌ Bad - Infrastructure concerns in domain
public class User : BaseEntity
{
    public void Activate()
    {
        Status = UserStatus.Active;
        _logger.LogInformation("User activated"); // ❌ External dependency
        _dbContext.SaveChanges(); // ❌ Persistence logic
    }
}
```

### 2. Application Layer

**Purpose**: Orchestrates domain objects to fulfill use cases
**Dependencies**: Domain Layer only
**Location**: `PurposePath.Application`

#### Application Layer Components

- **Application Services**: Coordinate domain objects for use cases
- **DTOs**: Data Transfer Objects for API contracts
- **Commands/Queries**: CQRS pattern implementation
- **Handlers**: Process commands and queries
- **Mappers**: Convert between domain objects and DTOs

#### Application Layer Guidelines

```csharp
// ✅ Good - Application service orchestrating domain logic
public class UserService
{
    public async Task<UserDto> CreateUserAsync(CreateUserRequest request)
    {
        // 1. Validate business rules
        var existingUser = await _userRepository.GetByEmailAsync(request.Email);
        if (existingUser != null)
            throw new BusinessException("User already exists");

        // 2. Create domain object
        var user = User.Create(request.Email, request.FirstName, request.LastName);

        // 3. Persist changes
        await _userRepository.AddAsync(user);
        
        // 4. Return DTO
        return UserDto.FromDomain(user);
    }
}
```

### 3. Infrastructure Layer

**Purpose**: Implements external concerns (database, external APIs, file system)
**Dependencies**: Domain and Application layers
**Location**: `PurposePath.Infrastructure`

#### Infrastructure Layer Components

- **Repository Implementations**: Concrete data access implementations
- **External Service Clients**: Third-party API integrations
- **Data Models**: Persistence-specific models (separate from domain models)
- **Mappers**: Convert between domain and persistence models

#### Domain vs Persistence Model Separation

```csharp
// Domain Model (Rich, behavior-focused)
public class User : BaseEntity
{
    public UserId Id { get; private set; }
    public Email Email { get; private set; }
    public string FirstName { get; private set; }
    public UserStatus Status { get; private set; }
    
    public void Activate() { /* business logic */ }
    public void ChangeEmail(Email newEmail) { /* validation logic */ }
}

// Persistence Model (Anemic, data-focused)
public class UserDataModel
{
    public string Id { get; set; }
    public string Email { get; set; }
    public string FirstName { get; set; }
    public string Status { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    
    // DynamoDB specific attributes
    [DynamoDBHashKey]
    public string PartitionKey { get; set; }
    
    [DynamoDBRangeKey]
    public string SortKey { get; set; }
}
```

### 4. API/Presentation Layer

**Purpose**: Handles HTTP requests/responses and API contracts
**Dependencies**: Application and Infrastructure layers
**Location**: `PurposePath.Api`

#### API/Presentation Layer Components

- **Controllers**: Handle HTTP requests
- **Middleware**: Cross-cutting concerns (logging, error handling)
- **API Models**: Request/response models
- **Validators**: Input validation

## DDD Patterns Implementation

### Value Objects

```csharp
public record Email
{
    public string Value { get; }
    
    public Email(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException("Email cannot be empty");
            
        if (!IsValidEmail(value))
            throw new ArgumentException("Invalid email format");
            
        Value = value.ToLowerInvariant().Trim();
    }
    
    private static bool IsValidEmail(string email) => 
        Regex.IsMatch(email, @"^[^@\s]+@[^@\s]+\.[^@\s]+$");
        
    public static implicit operator string(Email email) => email.Value;
}
```

### Entities with Strong IDs

```csharp
public record UserId(Guid Value)
{
    public static UserId New() => new(Guid.NewGuid());
    public static UserId From(string value) => new(Guid.Parse(value));
    public override string ToString() => Value.ToString();
}

public class User : BaseEntity
{
    public UserId Id { get; private set; }
    // ... other properties
    
    private User() { } // For ORM
    
    public User(UserId id, Email email, string firstName, string lastName, TenantId tenantId)
    {
        Id = id ?? throw new ArgumentNullException(nameof(id));
        Email = email ?? throw new ArgumentNullException(nameof(email));
        // ... validation and initialization
    }
}
```

### Domain Events

```csharp
public abstract record DomainEvent(DateTime OccurredAt = default)
{
    public DateTime OccurredAt { get; } = OccurredAt == default ? DateTime.UtcNow : OccurredAt;
}

public record UserCreatedEvent(UserId UserId, Email Email) : DomainEvent;

public abstract class BaseEntity
{
    private readonly List<DomainEvent> _domainEvents = new();
    public IReadOnlyCollection<DomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    
    protected void AddDomainEvent(DomainEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }
    
    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }
}
```

### Repository Pattern

```csharp
// Domain layer - Interface only
public interface IUserRepository
{
    Task<User?> GetByIdAsync(UserId id, CancellationToken cancellationToken = default);
    Task<User?> GetByEmailAsync(Email email, CancellationToken cancellationToken = default);
    Task AddAsync(User user, CancellationToken cancellationToken = default);
    Task UpdateAsync(User user, CancellationToken cancellationToken = default);
    Task DeleteAsync(UserId id, CancellationToken cancellationToken = default);
}

// Infrastructure layer - Implementation
public class DynamoDbUserRepository : IUserRepository
{
    private readonly IAmazonDynamoDB _dynamoDb;
    
    public async Task<User?> GetByIdAsync(UserId id, CancellationToken cancellationToken = default)
    {
        var dataModel = await GetUserDataModelAsync(id.ToString());
        return dataModel != null ? MapToDomain(dataModel) : null;
    }
    
    private User MapToDomain(UserDataModel dataModel)
    {
        // Convert persistence model to domain model
        return User.Restore(
            UserId.From(dataModel.Id),
            new Email(dataModel.Email),
            dataModel.FirstName,
            dataModel.LastName,
            TenantId.From(dataModel.TenantId),
            Enum.Parse<UserStatus>(dataModel.Status)
        );
    }
}
```

## Best Practices

### 1. Dependency Inversion

- High-level modules should not depend on low-level modules
- Both should depend on abstractions
- Domain layer defines interfaces, Infrastructure implements them

### 2. Single Responsibility Principle

- Each class should have one reason to change
- Separate concerns across different layers

### 3. No Primitive Obsession

- Use value objects instead of primitives for domain concepts
- `UserId` instead of `string`, `Email` instead of `string`

### 4. Fail Fast

- Validate inputs at domain boundaries
- Use guard clauses and throw meaningful exceptions

### 5. Immutability Where Possible

- Value objects should be immutable
- Use readonly fields and private setters

### 6. Testability

- Pure functions are easier to test
- Domain logic should be testable without external dependencies

## Error Handling Strategy

### Domain Exceptions

```csharp
public class DomainException : Exception
{
    public DomainException(string message) : base(message) { }
    public DomainException(string message, Exception innerException) : base(message, innerException) { }
}

public class BusinessRuleViolationException : DomainException
{
    public BusinessRuleViolationException(string rule, string details) 
        : base($"Business rule violation: {rule}. {details}") { }
}
```

### Application Layer Error Handling

```csharp
public class ApplicationException : Exception
{
    public ApplicationException(string message) : base(message) { }
}

public class EntityNotFoundException : ApplicationException
{
    public EntityNotFoundException(string entityName, string id) 
        : base($"{entityName} with ID '{id}' was not found.") { }
}
```

## Persistence Strategy

### DynamoDB Patterns

- Single Table Design where appropriate
- Separate tables for different aggregates
- Use composite keys (PK + SK) for relationships
- Implement optimistic concurrency with version fields

### Data Model Mapping

```csharp
public static class UserMapping
{
    public static UserDataModel ToDataModel(User user)
    {
        return new UserDataModel
        {
            Id = user.Id.ToString(),
            Email = user.Email.Value,
            FirstName = user.FirstName,
            LastName = user.LastName,
            Status = user.Status.ToString(),
            TenantId = user.TenantId.ToString(),
            CreatedAt = user.CreatedAt,
            UpdatedAt = user.UpdatedAt
        };
    }
    
    public static User ToDomain(UserDataModel dataModel)
    {
        return User.Restore(
            UserId.From(dataModel.Id),
            new Email(dataModel.Email),
            dataModel.FirstName,
            dataModel.LastName,
            TenantId.From(dataModel.TenantId),
            Enum.Parse<UserStatus>(dataModel.Status),
            dataModel.CreatedAt,
            dataModel.UpdatedAt
        );
    }
}
```

## Testing Strategy

### Unit Tests

- Domain logic should be 100% unit testable
- No external dependencies in domain tests
- Test business rules and invariants

### Integration Tests

- Test repository implementations against real database
- Test API endpoints end-to-end
- Use TestContainers for isolated testing

### Architecture Tests

```csharp
[Test]
public void Domain_Should_Not_Have_Dependencies_On_Other_Layers()
{
    var domainAssembly = Assembly.LoadFrom("PurposePath.Domain.dll");
    var dependencies = domainAssembly.GetReferencedAssemblies();
    
    dependencies.Should().NotContain(dep => 
        dep.Name.StartsWith("PurposePath.Application") ||
        dep.Name.StartsWith("PurposePath.Infrastructure") ||
        dep.Name.StartsWith("PurposePath.Api"));
}
```

## Migration Guidelines

### Phase 1: Core Domain

1. User Management (Users, Authentication)
2. Tenant Management (Organizations, Multi-tenancy)
3. Subscription Management (Billing, Plans)

### Phase 2: Business Logic

1. Account Management
2. Stripe Integration
3. Traction Features

### Phase 3: AI/Coaching Integration

1. Python-C# Communication Layer
2. Shared Data Models
3. Event-Driven Architecture

## Coding Standards

### Naming Conventions

- PascalCase for public members
- camelCase for private fields with underscore prefix
- Meaningful names over comments
- Avoid abbreviations

### File Organization

```text
PurposePath.Domain/
├── Entities/
├── ValueObjects/
├── Repositories/
├── Services/
├── Events/
└── Exceptions/

PurposePath.Application/
├── Services/
├── DTOs/
├── Commands/
├── Queries/
└── Mappers/

PurposePath.Infrastructure/
├── Repositories/
├── DataModels/
├── ExternalServices/
└── Configuration/
```

This architecture ensures:

- Clear separation of concerns
- High testability
- Maintainable codebase
- Strong typing throughout
- Zero dictionary usage (as per original requirement)
- Proper domain modeling following DDD principles
