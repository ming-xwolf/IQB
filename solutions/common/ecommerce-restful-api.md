# 通用面试 - 电商RESTful API设计完整实现

[← 返回API设计面试题](../../questions/backend/api-design.md)

## 🎯 解决方案概述

电商RESTful API设计是现代Web应用的核心，涉及资源建模、状态管理、安全认证、性能优化等关键技术。本方案展示了企业级电商API的完整设计实现，包含用户管理、商品管理、订单处理、支付集成等核心业务模块。

## 💡 核心问题分析

### 电商RESTful API的技术挑战

**业务背景**：电商平台需要支持用户注册登录、商品浏览、购物车管理、订单处理、支付结算等复杂业务流程

**技术难点**：
- RESTful设计原则与复杂业务逻辑的平衡
- API版本管理和向后兼容性保证
- 高并发场景下的接口性能优化
- 数据一致性和事务处理机制
- 安全认证和权限控制体系

## 📝 题目解决方案

### 解决方案思路分析

#### 1. RESTful API设计原则

**核心设计理念**：
- **资源导向**：以业务实体为中心设计API端点
- **统一接口**：使用标准HTTP方法和状态码
- **无状态性**：每个请求包含完整的处理信息
- **可缓存性**：合理使用HTTP缓存机制

#### 2. API架构设计策略

**分层架构模式**：
- **控制器层**：处理HTTP请求和响应
- **服务层**：业务逻辑处理和规则验证
- **数据访问层**：数据库操作和数据映射
- **集成层**：第三方服务调用和消息队列

#### 3. 数据建模和关系设计

**核心实体关系**：
- 用户(User) ← 一对多 → 订单(Order)
- 商品(Product) ← 多对多 → 分类(Category)
- 订单(Order) ← 一对多 → 订单项(OrderItem)
- 用户(User) ← 一对一 → 购物车(Cart)

### 代码实现要点

#### 电商RESTful API核心实现

```java
/**
 * 电商RESTful API完整实现
 * 
 * 设计原理：
 * 1. 基于Spring Boot和Spring Data JPA
 * 2. 完整的RESTful资源设计
 * 3. 统一的异常处理和响应格式
 * 4. JWT认证和角色权限控制
 */

// ==================== 数据模型定义 ====================

/**
 * 用户实体
 */
@Entity
@Table(name = "users")
@Data
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String username;
    
    @Column(unique = true, nullable = false)
    private String email;
    
    @Column(nullable = false)
    private String password;
    
    @Column(name = "full_name")
    private String fullName;
    
    private String phone;
    
    @Enumerated(EnumType.STRING)
    private UserRole role = UserRole.CUSTOMER;
    
    @Enumerated(EnumType.STRING)
    private UserStatus status = UserStatus.ACTIVE;
    
    @CreationTimestamp
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    @JsonIgnore
    private List<Order> orders = new ArrayList<>();
}

/**
 * 商品实体
 */
@Entity
@Table(name = "products")
@Data
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal price;
    
    @Column(name = "stock_quantity")
    private Integer stockQuantity;
    
    private String imageUrl;
    
    @Column(nullable = false)
    private String sku;
    
    @Enumerated(EnumType.STRING)
    private ProductStatus status = ProductStatus.ACTIVE;
    
    @CreationTimestamp
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @ManyToMany
    @JoinTable(
        name = "product_categories",
        joinColumns = @JoinColumn(name = "product_id"),
        inverseJoinColumns = @JoinColumn(name = "category_id")
    )
    private Set<Category> categories = new HashSet<>();
}

/**
 * 订单实体
 */
@Entity
@Table(name = "orders")
@Data
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String orderNumber;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;
    
    @Enumerated(EnumType.STRING)
    private OrderStatus status = OrderStatus.PENDING;
    
    @Column(name = "total_amount", precision = 10, scale = 2)
    private BigDecimal totalAmount;
    
    @Column(name = "shipping_address", columnDefinition = "TEXT")
    private String shippingAddress;
    
    @Column(name = "payment_method")
    private String paymentMethod;
    
    @Enumerated(EnumType.STRING)
    private PaymentStatus paymentStatus = PaymentStatus.PENDING;
    
    @CreationTimestamp
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> orderItems = new ArrayList<>();
}

// ==================== 枚举定义 ====================

public enum UserRole {
    CUSTOMER, ADMIN, SELLER
}

public enum UserStatus {
    ACTIVE, INACTIVE, BANNED
}

public enum ProductStatus {
    ACTIVE, INACTIVE, OUT_OF_STOCK
}

public enum OrderStatus {
    PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
}

public enum PaymentStatus {
    PENDING, PAID, FAILED, REFUNDED
}

// ==================== DTO类定义 ====================

/**
 * 统一API响应格式
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ApiResponse<T> {
    private boolean success;
    private String message;
    private T data;
    private String timestamp;
    
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(true, "操作成功", data, LocalDateTime.now().toString());
    }
    
    public static <T> ApiResponse<T> success(String message, T data) {
        return new ApiResponse<>(true, message, data, LocalDateTime.now().toString());
    }
    
    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, message, null, LocalDateTime.now().toString());
    }
}

/**
 * 用户注册请求DTO
 */
@Data
public class UserRegistrationRequest {
    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度应在3-50个字符之间")
    private String username;
    
    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;
    
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 100, message = "密码长度应在6-100个字符之间")
    private String password;
    
    private String fullName;
    private String phone;
}

/**
 * 商品创建请求DTO
 */
@Data
public class ProductCreateRequest {
    @NotBlank(message = "商品名称不能为空")
    private String name;
    
    private String description;
    
    @NotNull(message = "价格不能为空")
    @DecimalMin(value = "0.01", message = "价格必须大于0")
    private BigDecimal price;
    
    @Min(value = 0, message = "库存数量不能为负数")
    private Integer stockQuantity;
    
    private String imageUrl;
    
    @NotBlank(message = "SKU不能为空")
    private String sku;
    
    private Set<Long> categoryIds;
}

/**
 * 订单创建请求DTO
 */
@Data
public class OrderCreateRequest {
    @NotEmpty(message = "订单项不能为空")
    private List<OrderItemRequest> items;
    
    @NotBlank(message = "收货地址不能为空")
    private String shippingAddress;
    
    private String paymentMethod;
}

@Data
public class OrderItemRequest {
    @NotNull(message = "商品ID不能为空")
    private Long productId;
    
    @Min(value = 1, message = "数量必须大于0")
    private Integer quantity;
}

// ==================== 控制器实现 ====================

/**
 * 用户管理API控制器
 */
@RestController
@RequestMapping("/api/v1/users")
@CrossOrigin(origins = "*")
@Validated
public class UserController {
    
    @Autowired
    private UserService userService;
    
    /**
     * 用户注册
     * POST /api/v1/users/register
     */
    @PostMapping("/register")
    public ResponseEntity<ApiResponse<User>> registerUser(
            @Valid @RequestBody UserRegistrationRequest request) {
        
        User user = userService.registerUser(request);
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(ApiResponse.success("用户注册成功", user));
    }
    
    /**
     * 用户登录
     * POST /api/v1/users/login
     */
    @PostMapping("/login")
    public ResponseEntity<ApiResponse<Map<String, Object>>> loginUser(
            @Valid @RequestBody UserLoginRequest request) {
        
        Map<String, Object> result = userService.authenticateUser(request);
        return ResponseEntity.ok(ApiResponse.success("登录成功", result));
    }
    
    /**
     * 获取用户详情
     * GET /api/v1/users/{id}
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or #id == authentication.principal.id")
    public ResponseEntity<ApiResponse<User>> getUserById(@PathVariable Long id) {
        User user = userService.findById(id);
        return ResponseEntity.ok(ApiResponse.success(user));
    }
    
    /**
     * 更新用户信息
     * PUT /api/v1/users/{id}
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or #id == authentication.principal.id")
    public ResponseEntity<ApiResponse<User>> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody UserUpdateRequest request) {
        
        User user = userService.updateUser(id, request);
        return ResponseEntity.ok(ApiResponse.success("用户信息更新成功", user));
    }
    
    /**
     * 分页获取用户列表（管理员功能）
     * GET /api/v1/users?page=0&size=20&sort=id&direction=desc
     */
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Page<User>>> getUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "id") String sort,
            @RequestParam(defaultValue = "desc") String direction) {
        
        Pageable pageable = PageRequest.of(page, size, 
            Sort.Direction.fromString(direction), sort);
        Page<User> users = userService.findAll(pageable);
        
        return ResponseEntity.ok(ApiResponse.success(users));
    }
}

/**
 * 商品管理API控制器
 */
@RestController
@RequestMapping("/api/v1/products")
@CrossOrigin(origins = "*")
@Validated
public class ProductController {
    
    @Autowired
    private ProductService productService;
    
    /**
     * 创建商品
     * POST /api/v1/products
     */
    @PostMapping
    @PreAuthorize("hasRole('ADMIN') or hasRole('SELLER')")
    public ResponseEntity<ApiResponse<Product>> createProduct(
            @Valid @RequestBody ProductCreateRequest request) {
        
        Product product = productService.createProduct(request);
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(ApiResponse.success("商品创建成功", product));
    }
    
    /**
     * 获取商品详情
     * GET /api/v1/products/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Product>> getProductById(@PathVariable Long id) {
        Product product = productService.findById(id);
        return ResponseEntity.ok(ApiResponse.success(product));
    }
    
    /**
     * 更新商品信息
     * PUT /api/v1/products/{id}
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or hasRole('SELLER')")
    public ResponseEntity<ApiResponse<Product>> updateProduct(
            @PathVariable Long id,
            @Valid @RequestBody ProductUpdateRequest request) {
        
        Product product = productService.updateProduct(id, request);
        return ResponseEntity.ok(ApiResponse.success("商品更新成功", product));
    }
    
    /**
     * 删除商品
     * DELETE /api/v1/products/{id}
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Void>> deleteProduct(@PathVariable Long id) {
        productService.deleteProduct(id);
        return ResponseEntity.ok(ApiResponse.success("商品删除成功", null));
    }
    
    /**
     * 分页搜索商品
     * GET /api/v1/products?keyword=手机&categoryId=1&minPrice=100&maxPrice=5000
     */
    @GetMapping
    public ResponseEntity<ApiResponse<Page<Product>>> searchProducts(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Long categoryId,
            @RequestParam(required = false) BigDecimal minPrice,
            @RequestParam(required = false) BigDecimal maxPrice,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "createdAt") String sort,
            @RequestParam(defaultValue = "desc") String direction) {
        
        ProductSearchCriteria criteria = ProductSearchCriteria.builder()
            .keyword(keyword)
            .categoryId(categoryId)
            .minPrice(minPrice)
            .maxPrice(maxPrice)
            .build();
            
        Pageable pageable = PageRequest.of(page, size, 
            Sort.Direction.fromString(direction), sort);
        
        Page<Product> products = productService.searchProducts(criteria, pageable);
        return ResponseEntity.ok(ApiResponse.success(products));
    }
}

/**
 * 订单管理API控制器
 */
@RestController
@RequestMapping("/api/v1/orders")
@CrossOrigin(origins = "*")
@Validated
public class OrderController {
    
    @Autowired
    private OrderService orderService;
    
    /**
     * 创建订单
     * POST /api/v1/orders
     */
    @PostMapping
    @PreAuthorize("hasRole('CUSTOMER')")
    public ResponseEntity<ApiResponse<Order>> createOrder(
            @Valid @RequestBody OrderCreateRequest request,
            Authentication authentication) {
        
        Long userId = ((UserPrincipal) authentication.getPrincipal()).getId();
        Order order = orderService.createOrder(userId, request);
        
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(ApiResponse.success("订单创建成功", order));
    }
    
    /**
     * 获取订单详情
     * GET /api/v1/orders/{id}
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or @orderService.isOrderOwner(#id, authentication.principal.id)")
    public ResponseEntity<ApiResponse<Order>> getOrderById(@PathVariable Long id) {
        Order order = orderService.findById(id);
        return ResponseEntity.ok(ApiResponse.success(order));
    }
    
    /**
     * 更新订单状态
     * PATCH /api/v1/orders/{id}/status
     */
    @PatchMapping("/{id}/status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Order>> updateOrderStatus(
            @PathVariable Long id,
            @Valid @RequestBody OrderStatusUpdateRequest request) {
        
        Order order = orderService.updateOrderStatus(id, request.getStatus());
        return ResponseEntity.ok(ApiResponse.success("订单状态更新成功", order));
    }
    
    /**
     * 取消订单
     * PATCH /api/v1/orders/{id}/cancel
     */
    @PatchMapping("/{id}/cancel")
    @PreAuthorize("@orderService.isOrderOwner(#id, authentication.principal.id)")
    public ResponseEntity<ApiResponse<Order>> cancelOrder(@PathVariable Long id) {
        Order order = orderService.cancelOrder(id);
        return ResponseEntity.ok(ApiResponse.success("订单取消成功", order));
    }
    
    /**
     * 获取用户订单列表
     * GET /api/v1/orders/user/{userId}?status=PENDING&page=0&size=10
     */
    @GetMapping("/user/{userId}")
    @PreAuthorize("hasRole('ADMIN') or #userId == authentication.principal.id")
    public ResponseEntity<ApiResponse<Page<Order>>> getUserOrders(
            @PathVariable Long userId,
            @RequestParam(required = false) OrderStatus status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        
        Pageable pageable = PageRequest.of(page, size, 
            Sort.by(Sort.Direction.DESC, "createdAt"));
        
        Page<Order> orders = orderService.findUserOrders(userId, status, pageable);
        return ResponseEntity.ok(ApiResponse.success(orders));
    }
    
    /**
     * 订单支付
     * POST /api/v1/orders/{id}/payment
     */
    @PostMapping("/{id}/payment")
    @PreAuthorize("@orderService.isOrderOwner(#id, authentication.principal.id)")
    public ResponseEntity<ApiResponse<Map<String, Object>>> processPayment(
            @PathVariable Long id,
            @Valid @RequestBody PaymentRequest request) {
        
        Map<String, Object> result = orderService.processPayment(id, request);
        return ResponseEntity.ok(ApiResponse.success("支付处理成功", result));
    }
}

// ==================== 服务层实现示例 ====================

/**
 * 用户服务实现
 */
@Service
@Transactional
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private PasswordEncoder passwordEncoder;
    
    @Autowired
    private JwtTokenProvider jwtTokenProvider;
    
    /**
     * 用户注册
     */
    public User registerUser(UserRegistrationRequest request) {
        // 检查用户名和邮箱是否已存在
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new BusinessException("用户名已存在");
        }
        
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new BusinessException("邮箱已被注册");
        }
        
        // 创建新用户
        User user = new User();
        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setFullName(request.getFullName());
        user.setPhone(request.getPhone());
        user.setRole(UserRole.CUSTOMER);
        user.setStatus(UserStatus.ACTIVE);
        
        return userRepository.save(user);
    }
    
    /**
     * 用户认证
     */
    public Map<String, Object> authenticateUser(UserLoginRequest request) {
        User user = userRepository.findByUsernameOrEmail(
            request.getUsernameOrEmail(), request.getUsernameOrEmail())
            .orElseThrow(() -> new BusinessException("用户名或密码错误"));
        
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BusinessException("用户名或密码错误");
        }
        
        if (user.getStatus() != UserStatus.ACTIVE) {
            throw new BusinessException("账户已被禁用");
        }
        
        // 生成JWT Token
        String token = jwtTokenProvider.generateToken(user);
        
        Map<String, Object> result = new HashMap<>();
        result.put("token", token);
        result.put("user", user);
        result.put("expiresIn", jwtTokenProvider.getExpirationInSeconds());
        
        return result;
    }
    
    public User findById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new BusinessException("用户不存在"));
    }
    
    public Page<User> findAll(Pageable pageable) {
        return userRepository.findAll(pageable);
    }
    
    // 其他服务方法...
}

// ==================== 全局异常处理 ====================

/**
 * 全局异常处理器
 */
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusinessException(BusinessException e) {
        return ResponseEntity.badRequest()
            .body(ApiResponse.error(e.getMessage()));
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Map<String, String>>> handleValidationException(
            MethodArgumentNotValidException e) {
        
        Map<String, String> errors = new HashMap<>();
        e.getBindingResult().getFieldErrors().forEach(error -> 
            errors.put(error.getField(), error.getDefaultMessage()));
        
        return ResponseEntity.badRequest()
            .body(ApiResponse.error("参数验证失败"));
    }
    
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiResponse<Void>> handleAccessDeniedException(AccessDeniedException e) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
            .body(ApiResponse.error("访问被拒绝"));
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(Exception e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponse.error("系统内部错误"));
    }
}

/**
 * 业务异常类
 */
public class BusinessException extends RuntimeException {
    public BusinessException(String message) {
        super(message);
    }
} 