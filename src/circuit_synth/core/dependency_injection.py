"""
Dependency Injection Container

Provides a centralized container for managing dependencies and implementing
the dependency inversion principle throughout the Circuit_Synth application.

This container eliminates circular dependencies by allowing modules to depend
on abstractions rather than concrete implementations.
"""

import inspect
import logging
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar

# Import all interfaces from local module
from ._interfaces import (
    AgentFactory,  # KiCad Integration; Circuit Models; Intelligence System
)
from ._interfaces import (
    CircuitModelFactory,
    ComponentModelFactory,
    IAgent,
    IAgentManager,
    ICircuitModel,
    IComponentModel,
    IFootprintLibrary,
    IKiCadIntegration,
    IKnowledgeBase,
    ILLMManager,
    ILLMProvider,
    INetModel,
    IPCBGenerator,
    IPinModel,
    IPromptManager,
    IPromptTemplate,
    ISchematicGenerator,
    ISymbolLibrary,
    KnowledgeBaseFactory,
    LLMProviderFactory,
    NetModelFactory,
    PinModelFactory,
    PromptManagerFactory,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LifetimeScope:
    """Defines the lifetime scope for dependencies"""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DependencyRegistration:
    """Represents a dependency registration"""

    def __init__(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None,
        lifetime: str = LifetimeScope.TRANSIENT,
        dependencies: Optional[Dict[str, Type]] = None,
    ):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        self.dependencies = dependencies or {}

        # Validation
        if not any([implementation, factory, instance]):
            raise ValueError("Must provide implementation, factory, or instance")

        if sum(bool(x) for x in [implementation, factory, instance]) > 1:
            raise ValueError(
                "Can only provide one of implementation, factory, or instance"
            )


class IDependencyContainer(ABC):
    """Abstract interface for dependency container"""

    @abstractmethod
    def register(self, registration: DependencyRegistration) -> None:
        """Register a dependency"""
        pass

    @abstractmethod
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton dependency"""
        pass

    @abstractmethod
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient dependency"""
        pass

    @abstractmethod
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function"""
        pass

    @abstractmethod
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance"""
        pass

    @abstractmethod
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency"""
        pass

    @abstractmethod
    def is_registered(self, interface: Type[T]) -> bool:
        """Check if an interface is registered"""
        pass


class DependencyContainer(IDependencyContainer):
    """
    Concrete implementation of dependency injection container.

    Provides registration and resolution of dependencies with support for
    different lifetime scopes and automatic dependency injection.
    """

    def __init__(self):
        self._registrations: Dict[Type, DependencyRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = Lock()
        self._resolving: set = set()  # Track circular dependency resolution

    def register(self, registration: DependencyRegistration) -> None:
        """Register a dependency"""
        with self._lock:
            self._registrations[registration.interface] = registration
            logger.debug(
                f"Registered {registration.interface.__name__} with {registration.lifetime} lifetime"
            )

    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton dependency"""
        registration = DependencyRegistration(
            interface=interface,
            implementation=implementation,
            lifetime=LifetimeScope.SINGLETON,
        )
        self.register(registration)

    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient dependency"""
        registration = DependencyRegistration(
            interface=interface,
            implementation=implementation,
            lifetime=LifetimeScope.TRANSIENT,
        )
        self.register(registration)

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function"""
        registration = DependencyRegistration(
            interface=interface, factory=factory, lifetime=LifetimeScope.TRANSIENT
        )
        self.register(registration)

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance"""
        registration = DependencyRegistration(
            interface=interface, instance=instance, lifetime=LifetimeScope.SINGLETON
        )
        self.register(registration)
        # Store in singletons immediately
        with self._lock:
            self._singletons[interface] = instance

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency"""
        # Check for circular dependencies
        if interface in self._resolving:
            raise ValueError(f"Circular dependency detected for {interface.__name__}")

        # Check if it's a singleton that's already created
        if interface in self._singletons:
            return self._singletons[interface]

        # Get registration
        if interface not in self._registrations:
            raise ValueError(f"No registration found for {interface.__name__}")

        registration = self._registrations[interface]

        try:
            self._resolving.add(interface)

            # Create instance based on registration type
            if registration.instance is not None:
                instance = registration.instance
            elif registration.factory is not None:
                instance = registration.factory()
            elif registration.implementation is not None:
                instance = self._create_instance(registration.implementation)
            else:
                raise ValueError(f"Invalid registration for {interface.__name__}")

            # Store singleton
            if registration.lifetime == LifetimeScope.SINGLETON:
                with self._lock:
                    self._singletons[interface] = instance

            return instance

        finally:
            self._resolving.discard(interface)

    def _create_instance(self, implementation: Type[T]) -> T:
        """Create an instance with dependency injection"""
        # Get constructor signature
        sig = inspect.signature(implementation.__init__)

        # Resolve constructor dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Check if parameter has type annotation
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation

                # Try to resolve the dependency
                if self.is_registered(param_type):
                    kwargs[param_name] = self.resolve(param_type)
                elif param.default != inspect.Parameter.empty:
                    # Use default value if available
                    continue
                else:
                    logger.warning(
                        f"Cannot resolve dependency {param_type.__name__} for {implementation.__name__}"
                    )

        return implementation(**kwargs)

    def is_registered(self, interface: Type[T]) -> bool:
        """Check if an interface is registered"""
        return interface in self._registrations

    def get_registrations(self) -> Dict[Type, DependencyRegistration]:
        """Get all registrations (for debugging)"""
        return self._registrations.copy()

    def clear(self) -> None:
        """Clear all registrations and singletons"""
        with self._lock:
            self._registrations.clear()
            self._singletons.clear()
            self._resolving.clear()


class ServiceLocator:
    """
    Service locator pattern implementation for global access to the container.

    Provides a global point of access to the dependency container while
    maintaining testability through container replacement.
    """

    _container: Optional[IDependencyContainer] = None
    _lock = Lock()

    @classmethod
    def set_container(cls, container: IDependencyContainer) -> None:
        """Set the global container"""
        with cls._lock:
            cls._container = container

    @classmethod
    def get_container(cls) -> IDependencyContainer:
        """Get the global container"""
        if cls._container is None:
            with cls._lock:
                if cls._container is None:
                    cls._container = DependencyContainer()
        return cls._container

    @classmethod
    def resolve(cls, interface: Type[T]) -> T:
        """Resolve a dependency from the global container"""
        return cls.get_container().resolve(interface)

    @classmethod
    def is_registered(cls, interface: Type[T]) -> bool:
        """Check if an interface is registered in the global container"""
        return cls.get_container().is_registered(interface)


def configure_default_dependencies(container: IDependencyContainer) -> None:
    """
    Configure default dependencies for the Circuit_Synth application.

    This function sets up the basic dependency registrations that are
    commonly needed throughout the application.
    """
    logger.info("Configuring default dependencies...")

    # Note: Actual implementations would be registered here
    # For now, we're just setting up the container structure

    # Example registrations (would be replaced with actual implementations):
    # container.register_singleton(ILLMManager, LLMManager)
    # container.register_singleton(IAgentManager, AgentManager)
    # container.register_singleton(IKnowledgeBase, KnowledgeBase)
    # container.register_transient(ICircuitModel, CircuitModel)

    logger.info("Default dependencies configured")


def get_service(interface: Type[T]) -> T:
    """
    Convenience function to resolve a service from the global container.

    This provides a simple way to access dependencies without directly
    using the ServiceLocator.
    """
    return ServiceLocator.resolve(interface)


def inject(interface: Type[T]) -> Callable[[Callable], Callable]:
    """
    Decorator for automatic dependency injection.

    Usage:
        @inject(ILLMProvider)
        def my_function(llm_provider: ILLMProvider):
            # Use llm_provider
            pass
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if interface.__name__.lower() not in kwargs:
                kwargs[interface.__name__.lower()] = get_service(interface)
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Global container instance
_global_container = ServiceLocator.get_container()
